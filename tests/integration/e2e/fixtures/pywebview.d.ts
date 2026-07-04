declare global {
  interface Window {
    pywebview: {
      api: {
        get_app_info: () => Promise<{
          version: string;
          name: string;
        }>;
        load_settings: () => Promise<{
          urls_text: string;
          mode: string;
          word_limit: number;
          request_delay: number;
          include: string;
          exclude: string;
          max_pages: number;
          timeout_seconds: number;
          log_level: string;
        }>;
        start_execution: (form: unknown) => Promise<{ status: string }>;
        get_status: (args: { since_index: number }) => Promise<{
          state: string;
          log_lines: string[];
          last_index: number;
          sites_done: number;
          result_summary: {
            total_urls: number;
            success_count: number;
          } | null;
        }>;
        open_log_folder: () => Promise<{ status: string }>;
      };
    };
  }
}

export {};
