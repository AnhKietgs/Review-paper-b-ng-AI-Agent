import type { Metadata } from "next";
import "./style.css";

export const metadata: Metadata = { title: "Paper Review Lab" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi"><body>{children}</body></html>;
}

