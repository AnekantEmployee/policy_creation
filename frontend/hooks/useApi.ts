import { useState, useCallback } from 'react';
import toast from 'react-hot-toast';

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface ExecOptions {
  successMessage?: string;
  errorMessage?: string;
}

export function useApi<T = unknown>() {
  const [state, setState] = useState<ApiState<T>>({ data: null, loading: false, error: null });

  const execute = useCallback(async (apiCall: () => Promise<T>, opts?: ExecOptions): Promise<T | null> => {
    setState({ data: null, loading: true, error: null });
    try {
      const result = await apiCall();
      setState({ data: result, loading: false, error: null });
      if (opts?.successMessage) toast.success(opts.successMessage);
      return result;
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { error?: string } }; message?: string })?.response?.data?.error ||
        (err as { message?: string })?.message ||
        'An unexpected error occurred';
      setState({ data: null, loading: false, error: msg });
      toast.error(opts?.errorMessage ?? msg);
      return null;
    }
  }, []);

  return { ...state, execute };
}
