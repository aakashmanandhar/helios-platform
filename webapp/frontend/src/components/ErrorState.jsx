export default function ErrorState({ message = 'Something went wrong loading this data.' }) {
  return (
    <div className="error-state">
      <span>⚠</span> {message}
    </div>
  );
}
