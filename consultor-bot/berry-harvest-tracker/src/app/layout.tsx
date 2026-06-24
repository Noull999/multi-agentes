import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'berry-harvest-tracker',
  description: 'Generated with AI assistance',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='es'>
      <body>{children}</body>
    </html>
  );
}
