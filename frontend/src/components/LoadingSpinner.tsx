export default function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center gap-4 py-16">
      <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-700 border-t-indigo-500" />
      <p className="text-gray-400 text-sm animate-pulse">
        Fetching data and running analysis pipeline...
      </p>
    </div>
  );
}
