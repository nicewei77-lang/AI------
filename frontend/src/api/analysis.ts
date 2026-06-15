import type {AnalysisJobResponse, AnalysisLatestResponse, AnalysisRunResponse} from "../types/analysis";
import {api, ApiError} from "./http";

export async function runAnalysis(postId: string): Promise<AnalysisRunResponse> {
    return api<AnalysisRunResponse>(`/posts/${postId}/analysis`, {
        method: "POST",
    });
}

export async function startAnalysisJob(postId: string): Promise<AnalysisJobResponse> {
    return api<AnalysisJobResponse>(`/posts/${postId}/analysis/jobs`, {
        method: "POST",
    });
}

export async function fetchAnalysisStatus(postId: string): Promise<AnalysisJobResponse> {
    return api<AnalysisJobResponse>(`/posts/${postId}/analysis/status`);
}

export async function fetchLatestAnalysis(postId: string): Promise<AnalysisLatestResponse | null> {
    try {
        return await api<AnalysisLatestResponse>(`/posts/${postId}/analysis/latest`);
    } catch (err) {
        if (
            err instanceof ApiError &&
            err.status === 404 &&
            err.detail === "analysis report not found"
        ) {
            return null;
        }
        throw err;
    }
}
