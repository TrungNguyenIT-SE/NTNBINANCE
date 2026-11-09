import { useEffect, useState } from "react";

type HealthState = "checking" | "ready" | "unavailable";

export function App() {
  const [health, setHealth] = useState<HealthState>("checking");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/health/ready", { signal: controller.signal })
      .then((response) => {
        setHealth(response.ok ? "ready" : "unavailable");
      })
      .catch(() => {
        if (!controller.signal.aborted) setHealth("unavailable");
      });
    return () => controller.abort();
  }, []);

  return (
    <main className="shell">
      <section className="card" aria-labelledby="title">
        <p className="eyebrow">LOCAL / PRIVATE / RESEARCH</p>
        <h1 id="title">NTN Binance Signal Research</h1>
        <p>
          Nền tảng kỹ thuật Stage C đã sẵn sàng. Tính năng upload và dự đoán sẽ được mở theo các
          Exit Gate tiếp theo.
        </p>
        <dl className="status-grid">
          <div>
            <dt>Backend</dt>
            <dd data-state={health}>{health}</dd>
          </div>
          <div>
            <dt>Trading</dt>
            <dd data-state="disabled">disabled</dd>
          </div>
          <div>
            <dt>Chi phí mới</dt>
            <dd>0 VNĐ</dd>
          </div>
        </dl>
        <p className="warning">Không phải cam kết lợi nhuận. MVP không đặt lệnh thật.</p>
      </section>
    </main>
  );
}
