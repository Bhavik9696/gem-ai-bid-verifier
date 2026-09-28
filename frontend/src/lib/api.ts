"use client";

import { useEffect, useState } from "react";

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export type Tender = {
  tenderId: string;
  title: string;
  referenceNumber: string;
  category: string;
  buyerOrganisation: string;
  publishedDate: string | null;
  bidClosingDate: string | null;
  estimatedValue: number | null;
  currency: string;
  status: string;
};

export type TenderDetail = Tender & {
  eligibilityConditions: Record<string, unknown>;
  mandatoryDocuments: string[];
  rulebookVersion: string;
};

export type Bid = {
  bidId: string;
  tenderId: string;
  bidderId: string;
  bidderName: string;
  submittedAt: string | null;
  bidAmount: number;
  currency: string;
  status: string;
  complianceScore: number | null;
  riskLevel: string | null;
  recommendation: string | null;
};

export type Assessment = {
  bidId: string;
  complianceScore: number;
  verificationCoverage: number;
  riskLevel: string;
  recommendation: string;
  recommendationSummary: string | null;
  hasMandatoryFailure: boolean;
  scoreBreakdown: Record<string, unknown>[];
  evaluatedAt: string;
  ruleResults: RuleResult[];
  findings: Finding[];
  verificationResults: VerificationResult[];
  extractedFacts: ExtractedFact[];
  auditEvents: AuditEvent[];
};

export type RuleResult = {
  id: string;
  ruleId: string;
  ruleName: string;
  clause: string | null;
  status: string;
  details: string | null;
  isMandatory: boolean;
};

export type Finding = {
  id: string;
  findingType: string;
  severity: string;
  message: string;
  evidenceReference: string | null;
};

export type VerificationResult = {
  id: string;
  source: string;
  mode: string;
  identifier: string;
  status: string;
  verifiedFacts: Record<string, unknown>;
  evidenceReference: string | null;
  checkedAt: string;
};

export type ExtractedFact = {
  id: string;
  field: string;
  value: string | null;
  confidence: number;
  documentId: string | null;
  page: number;
  evidence: string | null;
};

export type AuditEvent = {
  id: string;
  bidId: string;
  eventType: string;
  actor: string;
  details: Record<string, unknown>;
  timestamp: string;
};

export type OfficerDecision = {
  id: string;
  bidId: string;
  officerId: string;
  decision: string;
  reason: string | null;
  notes: string | null;
  decidedAt: string;
  bidStatus: string;
};

export type ApiState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, cache: "no-store" });
  } catch {
    throw new Error(`Cannot reach the ComplianceOS API at ${API_BASE_URL}. Check that the backend is running.`);
  }

  if (!response.ok) {
    let message = `API request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // Keep the HTTP status as the useful fallback.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function useApiData<T>(path: string | null): ApiState<T> {
  const [result, setResult] = useState<{ key: string; data: T | null; error: string | null } | null>(null);
  const [revision, setRevision] = useState(0);
  const key = `${path ?? ""}:${revision}`;

  useEffect(() => {
    let active = true;
    if (!path) return () => { active = false; };
    apiRequest<T>(path)
      .then(data => { if (active) setResult({ key, data, error: null }); })
      .catch(reason => { if (active) setResult({ key, data: null, error: reason instanceof Error ? reason.message : "Request failed" }); });
    return () => { active = false; };
  }, [path, key]);

  const current = result?.key === key ? result : null;
  return { data: current?.data ?? null, loading: Boolean(path) && !current, error: current?.error ?? null, reload: () => setRevision(value => value + 1) };
}

export function useBidWorkspace(bidId: string) {
  const [result, setResult] = useState<{ key: string; bid: Bid | null; assessment: Assessment | null; error: string | null } | null>(null);
  const [revision, setRevision] = useState(0);
  const key = `${bidId}:${revision}`;

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const tenders = await apiRequest<Tender[]>("/api/tenders");
        const bidsByTender = await Promise.all(
          tenders.map(tender => apiRequest<Bid[]>(`/api/tenders/${encodeURIComponent(tender.tenderId)}/bids`)),
        );
        const foundBid = bidsByTender.flat().find(item => item.bidId === bidId) ?? null;
        if (!foundBid) throw new Error(`Bid '${bidId}' was not found.`);

        let foundAssessment: Assessment | null = null;
        try {
          foundAssessment = await apiRequest<Assessment>(`/api/bids/${encodeURIComponent(bidId)}/assessment`);
        } catch (reason) {
          if (!(reason instanceof Error) || !reason.message.includes("No verification assessment")) throw reason;
        }
        if (active) {
          setResult({ key, bid: foundBid, assessment: foundAssessment, error: null });
        }
      } catch (reason) {
        if (active) setResult({ key, bid: null, assessment: null, error: reason instanceof Error ? reason.message : "Unable to load bid data." });
      }
    }

    void load();
    return () => { active = false; };
  }, [bidId, key]);

  const current = result?.key === key ? result : null;
  return {
    bid: current?.bid ?? null,
    assessment: current?.assessment ?? null,
    loading: !current,
    error: current?.error ?? null,
    reload: () => setRevision(value => value + 1),
  };
}

export async function runVerification(bidId: string): Promise<Assessment> {
  return apiRequest<Assessment>(`/api/bids/${encodeURIComponent(bidId)}/run-verification`, { method: "POST" });
}

export async function recordDecision(
  bidId: string,
  payload: { decision: "CONFIRM" | "REQUEST_CLARIFICATION" | "OVERRIDE"; reason?: string; notes?: string; officerId?: string },
): Promise<OfficerDecision> {
  return apiRequest<OfficerDecision>(`/api/bids/${encodeURIComponent(bidId)}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
