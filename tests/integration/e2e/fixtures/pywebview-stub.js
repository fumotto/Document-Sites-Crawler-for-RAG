window.pywebview = {
  api: {
    get_app_info: async function() {
      return { app_name: 'Document Sites Crawler for RAG', version: '0.1.0' };
    },
    load_settings: async function() {
      return {
        urls_text: '',
        mode: 'incremental',
        word_limit: 450000,
        request_delay: 0.5,
        include: '',
        exclude: '',
        max_pages: 1000,
        timeout_seconds: 30,
        log_level: 'INFO',
      };
    },
    start_execution: async function(form) {
      return { status: 'started' };
    },
    get_status: (() => {
      let calls = 0;
      const states = [
        {
          state: 'running',
          log_lines: ['Starting...'],
          last_index: 0,
          sites_done: 0,
          sites_total: 1,
          result_summary: null,
        },
        {
          state: 'running',
          log_lines: ['Crawling...'],
          last_index: 1,
          sites_done: 1,
          sites_total: 1,
          result_summary: null,
        },
        {
          state: 'completed',
          log_lines: ['Finished'],
          last_index: 2,
          sites_done: 1,
          sites_total: 1,
          result_summary: { total_urls: 1, success_count: 1, duplicate_excluded_count: 0, chunk_file_count: 1 },
        },
      ];
      return async function(lastIndex) {
        const result = states[Math.min(calls, states.length - 1)];
        calls += 1;
        return result;
      };
    })(),
    open_log_folder: async function() {
      return { status: 'opened' };
    },
  },
};
