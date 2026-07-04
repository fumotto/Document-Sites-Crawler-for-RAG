window.pywebview = {
  api: {
    get_app_info: async () => ({
      version: "0.1.0",
      name: "Document Sites Crawler for RAG",
    }),
    load_settings: async () => ({
      urls_text: "",
      mode: "incremental",
      word_limit: 450000,
      request_delay: 0.5,
      include: "",
      exclude: "",
      max_pages: 1000,
      timeout_seconds: 30,
      log_level: "INFO",
    }),
    start_execution: async (form: any) => ({ status: "started" }),
    get_status: async ({ since_index }: { since_index: number }) => {
      const states = [
        {
          state: "running",
          log_lines: ["Starting..."],
          last_index: 0,
          sites_done: 0,
          result_summary: null,
        },
        {
          state: "running",
          log_lines: ["Crawling..."],
          last_index: 1,
          sites_done: 1,
          result_summary: null,
        },
        {
          state: "completed",
          log_lines: ["Finished"],
          last_index: 2,
          sites_done: 1,
          result_summary: { total_urls: 1, success_count: 1 },
        },
      ];
      return states[Math.min(since_index + 1, states.length - 1)];
    },
    open_log_folder: async () => ({ status: "opened" }),
  },
};
