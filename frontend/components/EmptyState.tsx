export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-900/20 px-6 py-16 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-slate-800/60 text-slate-500">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" className="h-7 w-7">
          <path
            d="M9 12h6m-6 4h6m-8 4h10a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H9.83a2 2 0 0 0-1.42.59l-2.83 2.82A2 2 0 0 0 5 8.83V18a2 2 0 0 0 2 2Z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h3 className="text-sm font-semibold text-slate-200">
        Upload a document to start asking questions
      </h3>
      <p className="mt-1 max-w-sm text-sm text-slate-500">
        Once a PDF is processed and indexed, you can ask natural-language
        questions and get answers grounded in its content, with citations.
      </p>
    </div>
  );
}
