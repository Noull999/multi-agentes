import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '../consultor-outside-test',
  description: 'Generated with AI assistance',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='es'>
      <body>{children}</body>
    </html>
  );
}
