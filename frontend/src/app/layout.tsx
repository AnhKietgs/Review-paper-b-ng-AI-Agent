import type { Metadata } from "next";
import "./style.css";
import Shell from "@/components/shell";

export const metadata: Metadata = { title: "Paper Review Lab" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi"><body><Shell>{children}</Shell></body></html>;
}

