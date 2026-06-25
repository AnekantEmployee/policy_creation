import apiClient from './client';
import type { GeneratedPolicy, GeneratedProcedure } from '@/types';

/** Trigger a browser download from a blob URL */
function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href     = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * POST /export/docx
 * Used from the wizard StepResults after generation.
 */
export async function downloadWizardDocx(
  orgName:    string,
  frameworks: string[],
  policies:   GeneratedPolicy[],
  procedures: GeneratedProcedure[],
): Promise<void> {
  const response = await apiClient.post(
    '/export/docx',
    { org_name: orgName, frameworks, policies, procedures },
    { responseType: 'blob' },
  );
  const filename = `${orgName.replace(/\s+/g, '_')}_compliance.docx`;
  triggerDownload(response.data as Blob, filename);
}

/**
 * GET /export/session/:id/docx
 * Used from the History page to download a saved session.
 */
export async function downloadSessionDocx(
  sessionId: number,
  orgName:   string,
): Promise<void> {
  const response = await apiClient.get(
    `/export/session/${sessionId}/docx`,
    { responseType: 'blob' },
  );
  const filename = `${orgName.replace(/\s+/g, '_')}_session_${sessionId}.docx`;
  triggerDownload(response.data as Blob, filename);
}
