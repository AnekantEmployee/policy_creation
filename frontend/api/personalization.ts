import apiClient from './client';
import type { PersonalizationQuestion } from '@/types';

export interface GenerateQuestionsRequest {
  org_name: string;
  org_description: string;
  org_country: string;
  frameworks: string[];
  policy_types: string[];
  procedure_types: string[];
}

export const personalizationApi = {
  generateQuestions: async (req: GenerateQuestionsRequest): Promise<{ questions: PersonalizationQuestion[]; source: 'ai' | 'static' }> => {
    const { data } = await apiClient.post('/personalization/generate-questions', req);
    return data;
  },
};
