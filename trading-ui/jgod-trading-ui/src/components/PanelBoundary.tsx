import React from "react";

interface PanelBoundaryProps {
  title: string;
  children: React.ReactNode;
}

export class PanelBoundary extends React.Component<
  PanelBoundaryProps,
  { hasError: boolean; error?: unknown }
> {
  constructor(props: PanelBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: unknown) {
    return { hasError: true, error };
  }

  componentDidCatch(error: unknown) {
    console.error(`Panel "${this.props.title}" crashed:`, error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {this.props.title}
          </h2>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
            <div className="text-red-700 dark:text-red-400 font-semibold mb-2">
              {this.props.title} crashed (caught by PanelBoundary)
            </div>
            <div className="text-red-600 dark:text-red-500 text-sm mb-3">
              Try refresh. If it happens again, check console logs.
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

