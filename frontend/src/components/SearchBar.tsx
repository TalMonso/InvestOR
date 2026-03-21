import { useState, type FormEvent } from "react";

interface Props {
  onSearch: (ticker: string) => void;
  loading: boolean;
}

export default function SearchBar({ onSearch, loading }: Props) {
  const [value, setValue] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim().toUpperCase();
    if (trimmed) onSearch(trimmed);
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 w-full max-w-xl mx-auto">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Enter stock ticker (e.g. AAPL)"
        disabled={loading}
        className="flex-1 rounded-lg border border-gray-700 bg-gray-900 px-4 py-3 text-gray-100
                   placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-1
                   focus:ring-indigo-500 disabled:opacity-50 transition text-lg tracking-wide"
      />
      <button
        type="submit"
        disabled={loading || !value.trim()}
        className="rounded-lg bg-indigo-600 px-6 py-3 font-semibold text-white
                   hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed
                   transition cursor-pointer"
      >
        {loading ? "Analyzing..." : "Analyze"}
      </button>
    </form>
  );
}
