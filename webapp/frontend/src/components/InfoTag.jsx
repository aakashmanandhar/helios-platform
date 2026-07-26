import { Info } from 'lucide-react';

export default function InfoTag({ text }) {
  return (
    <span className="info-tag" title={text}>
      <Info size={12} />
    </span>
  );
}
