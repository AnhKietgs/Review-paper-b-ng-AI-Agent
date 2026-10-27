import Link from "next/link";
import { PageHeader } from "@/components/shell";

export default function Home() {
  return <><PageHeader eyebrow="EVIDENCE-GROUNDED REVIEW" title="Đọc sâu hơn. Nhận xét có nguồn." description="Phân tích bài báo, đối chiếu bằng chứng và hoàn thiện bản phản biện cùng AI." />
    <section className="hero"><div><span className="badge">PAPER REVIEW · MVP</span><h2>Từ bài báo gốc<br />đến bản review có thể kiểm chứng.</h2><p>Bạn chọn tài liệu và tiêu chí. Hệ thống gọi từng agent khi cần, lưu lại quá trình và đưa bằng chứng về đúng nguồn để bạn kiểm tra.</p><Link className="button" href="/papers">Bắt đầu với thư viện →</Link></div><div className="hero-flow">TÀI LIỆU GỐC<div>Supervisor</div><span>↓ gọi theo nhu cầu</span><div>Phân tích · So sánh · Kiểm chứng</div><span>↓ kiểm tra nguồn & duyệt</span><div>Bản review có bằng chứng</div></div></section>
    <div className="cards">{[["01", "Chuẩn bị", "Tải PDF hoặc DOCX có văn bản. Tự chọn công trình liên quan.", "/papers"], ["02", "Đặt tiêu chí", "Tạo rubric với các câu hỏi định tính, phù hợp với lĩnh vực.", "/rubrics"], ["03", "Review & kiểm chứng", "Theo dõi harness, sửa nhận xét và duyệt bản xuất Markdown.", "/reviews"]].map(([n,t,d,h]) => <Link className="panel step-card" href={h} key={n}><span className="step-number">{n}</span><h2>{t}</h2><p>{d}</p><span>Đi đến bước này →</span></Link>)}</div>
    <p className="muted">Literature Review và tìm kiếm Internet thuộc giai đoạn mở rộng.</p></>;
}
