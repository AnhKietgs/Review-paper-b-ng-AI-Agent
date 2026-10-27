"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";

export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [mode, setMode] = useState("đang kết nối");
  useEffect(() => { api<{llm_mode: string}>("/runtime").then(r => setMode(r.llm_mode)).catch(() => setMode("offline")); }, []);
  return <div className="app-shell"><aside className="sidebar">
    <Link href="/" className="brand">◧ Paper Review<small>RESEARCH WORKSPACE</small></Link>
    <p className="eyebrow">KHÔNG GIAN LÀM VIỆC</p>
    <nav>{[["/", "Tổng quan"], ["/papers", "Thư viện paper"], ["/rubrics", "Rubric đánh giá"], ["/reviews", "Bản review"]].map(([url, title], i) => <Link className={path === url || (url !== "/" && path.startsWith(url)) ? "active" : ""} key={url} href={url}><span>0{i + 1}</span>{title}</Link>)}</nav>
    <div className="sidebar-footer"><span className="badge">{mode.toUpperCase()}</span><p>{mode === "fixture" ? "Trả lời mô phỏng để kiểm tra quy trình. Không dùng như đánh giá khoa học." : mode === "groq" ? "Phân tích qua Groq. Kiểm tra bằng chứng trước khi duyệt." : "Kiểm tra kết nối backend."}</p><small>Local · Paper Review MVP</small></div>
  </aside><main>{children}</main></div>;
}
export function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return <header className="page-header"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></header>;
}
export function ErrorBanner({ message }: { message: string }) {
  return message ? <div role="alert" className="error">{message}</div> : null;
}
