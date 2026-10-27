"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PageHeader, ErrorBanner } from "@/components/shell";
import { api, errorMessage } from "@/lib/api/client";
import type { AcceptedRun, Evidence, Paper, Review } from "@/lib/api/types";

export default function ReviewDetail() {
  const { id } = useParams<{id:string}>(); const router = useRouter();
  const [review, setReview] = useState<Review|null>(null), [paper, setPaper] = useState<Paper|null>(null);
  const [source, setSource] = useState<{paper:Paper; evidence:Evidence}|null>(null);
  const [error, setError] = useState(""), [busy, setBusy] = useState(false), [dirty, setDirty] = useState(false), [notice, setNotice] = useState("");
  const [confirmations, setConfirmations] = useState<string[]>([]);
  useEffect(()=>{let alive=true; api<Review>(`/reviews/${id}`).then(async r=>{const p=await api<Paper>(`/papers/${r.paper_id}/versions/${r.paper_content_version}`);if(alive){setReview(r);setPaper(p);setDirty(false);}}).catch(e=>{if(alive)setError(errorMessage(e));});return()=>{alive=false;};},[id]);
  async function act(action:()=>Promise<void>) {setBusy(true);setError("");setNotice("");try{await action();}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
  async function run(mode:string) {await act(async()=>{const r=await api<AcceptedRun>(`/reviews/${id}/runs`,{method:"POST",body:JSON.stringify({mode})});router.push(`/runs/${r.run_id}`);});}
  async function save() {if(!review)return;await act(async()=>{setReview(await api<Review>(`/reviews/${id}`,{method:"PATCH",body:JSON.stringify({summary:review.summary,findings:review.findings})}));setDirty(false);setNotice("Đã lưu. Nhận xét thay đổi cần được kiểm chứng lại trước khi duyệt.");});}
  async function openSource(evidence:Evidence){await act(async()=>{const p=await api<Paper>(`/papers/${evidence.paper_id}/versions/${evidence.content_version}`);setSource({paper:p,evidence});});}
  if(!review)return <><PageHeader eyebrow="REVIEW WORKSPACE" title="Đang tải bản review…" description="Đọc phiên bản và bằng chứng đã lưu."/><ErrorBanner message={error}/></>;
  const locked=review.status==="approved"||["queued","running","interrupted"].includes(review.status);
  return <><PageHeader eyebrow={`REVIEW WORKSPACE / REVISION ${review.revision}`} title={paper?.title??"Bản review"} description={`Paper v${review.paper_content_version} · Rubric v${review.rubric_version} · ${review.references.length} công trình liên quan`}/>
    <ErrorBanner message={error}/>{notice&&<div role="status" className="notice">{notice}</div>}
    <section className="panel"><div className="spread"><span className={`status ${review.status}`}>{review.status}</span><span className="mono">{id.slice(0,8)}</span></div><div className="actions">
      <button disabled={busy||dirty||["queued","running","interrupted"].includes(review.status)} onClick={()=>run("review")}>Chạy Paper Review</button>
      {!locked&&review.findings.length>0&&<button className="secondary" disabled={busy||dirty} onClick={()=>run("verify")}>Kiểm chứng bản sửa</button>}
      <button className="secondary" disabled={busy||dirty} onClick={()=>act(async()=>{const r=await api<Review>(`/reviews/${id}/revisions`,{method:"POST"});router.push(`/reviews/${r.id}`);})}>Tạo revision mới</button>
      {review.status==="approved"&&<a className="button" download href={`/api/v1/reviews/${id}/export.md`}>Tải Markdown</a>}
      <Link href="/reviews">← Danh sách review</Link>
    </div><small>{dirty?"Có thay đổi chưa lưu. Lưu trước khi chạy hoặc duyệt.":"Mỗi lần chạy tạo một revision riêng. Bản đã duyệt không bị ghi đè."}</small></section>
    <div className="two-columns"><section className="panel"><h2>Nội dung đánh giá</h2><label>Tóm tắt biên tập<textarea disabled={locked} value={review.summary} onChange={e=>{setReview({...review,summary:e.target.value});setDirty(true);}}/></label>
      {!review.findings.length&&<p className="empty">Chạy Paper Review để tạo nhận xét và kiểm tra bằng chứng.</p>}
      {review.findings.map((f,i)=><article className="finding" key={f.id}><div className="spread"><strong>{f.criterion_code}</strong><span className={`status ${f.status}`}>{f.status}</span></div><label>Nhận xét {i+1}<textarea disabled={locked} value={f.claim} onChange={e=>{setReview({...review,findings:review.findings.map((item,j)=>j===i?{...item,claim:e.target.value}:item)});setDirty(true);}}/></label><small>{f.kind} · {f.verdict}</small>{f.evidence.map((ev,j)=><div key={`${ev.chunk_id}-${j}`}><blockquote>{ev.quote}</blockquote><button className="text-button" disabled={busy} onClick={()=>openSource(ev)}>Xem nguồn {j+1} · {ev.locator_type} {ev.locator_value} · v{ev.content_version} ↗</button></div>)}{!locked&&f.status==="needs_human_review"&&<label className="inline"><input type="checkbox" checked={confirmations.includes(f.id)} onChange={e=>setConfirmations(e.target.checked?[...confirmations,f.id]:confirmations.filter(x=>x!==f.id))}/>Tôi đã kiểm tra nhận xét {i+1}; giữ nhãn chưa chắc chắn khi duyệt.</label>}</article>)}
      {!locked&&<div className="actions"><button className="secondary" disabled={busy||!dirty} onClick={save}>Lưu chỉnh sửa</button><button disabled={busy||dirty||!review.findings.length} onClick={()=>act(async()=>{setReview(await api<Review>(`/reviews/${id}/approve`,{method:"POST",body:JSON.stringify({confirmations})}));setNotice("Đã duyệt và đóng băng bản xuất Markdown.");})}>Duyệt bản review</button></div>}
      <details><summary>Phân tích và phạm vi đọc</summary><pre>{JSON.stringify(review.analysis,null,2)}</pre></details>
    </section><section className="panel source-viewer" data-testid="source-viewer"><h2>Đối chiếu tài liệu gốc</h2>{source?<><h3>{source.paper.title}</h3><p><span className="badge">v{source.evidence.content_version} · {source.evidence.locator_type} {source.evidence.locator_value}</span></p><a href={`/api/v1/papers/${source.paper.id}/source?version=${source.evidence.content_version}`} target="_blank" rel="noreferrer">Mở / tải tệp gốc ↗</a>{source.paper.media_type==="application/pdf"&&<iframe title="Tài liệu PDF gốc" src={`/api/v1/papers/${source.paper.id}/source?version=${source.evidence.content_version}#page=${source.evidence.locator_value}`}/>}<div className="source-chunk highlight">{source.paper.chunks.find(c=>c.id===source.evidence.chunk_id)?.text??"Không tìm thấy đoạn nguồn."}</div><small>Vị trí được lấy từ phiên bản tài liệu lúc chạy review, không phải bản mới nhất trong thư viện.</small></>:<p className="empty">Bấm “Xem nguồn” dưới một nhận xét để đối chiếu nội dung.</p>}</section></div></>;
}
