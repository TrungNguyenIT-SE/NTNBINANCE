# Hướng dẫn chụp ảnh biểu đồ v1

## Trước khi chụp

1. Mở chart nến BTCUSDT hoặc ETHUSDT USDⓈ-M perpetual trên Binance/TradingView.
2. Chuẩn bị đúng hai ảnh: một ảnh `1H`, một ảnh `15m`, cùng symbol.
3. Chụp hai ảnh trong vòng 2 phút và gửi ngay; dùng đồng hồ hệ thống đã đồng bộ.
4. Với 1H, hiển thị ít nhất 60 nến đã đóng (khuyến nghị 80). Với 15m, hiển thị ít nhất 80
   nến đã đóng (khuyến nghị 96).

## Ảnh đạt yêu cầu

- PNG/JPEG/WebP, tối đa 10 MiB.
- Rộng 800–4096 px, cao 600–4096 px, tối đa 16.777.216 pixel sau decode.
- Nhìn rõ symbol, timeframe, nến và râu nến, trục giá bên phải, trục thời gian phía dưới.
- Chart chính chiếm phần lớn ảnh; dark/light đều được nếu tương phản rõ.
- Không để tooltip, menu, hộp đặt lệnh hoặc cửa sổ khác che vùng nến mới nhất.

## Không gửi

- Ảnh mờ, crop mất symbol/timeframe/trục giá/trục thời gian hoặc chỉ có line chart.
- Hai ảnh khác symbol, gán nhầm timeframe hoặc chụp cách nhau quá 2 phút.
- Ảnh chứa API key, UID, email, số dư hay dữ liệu cá nhân không cần thiết.
- SVG, PDF, GIF/ảnh động, HEIC hoặc file chỉ đổi đuôi thành `.png`.

## Metadata cần khai báo

- Symbol: `BTCUSDT` hoặc `ETHUSDT`.
- Ảnh nào là `1H`, ảnh nào là `15m`.
- Thời điểm chụp có múi giờ; ưu tiên UTC.
- Nguồn ảnh: Binance, TradingView hoặc Unknown.
- Nếu biết, chọn loại giá đang hiển thị: contract, mark hoặc index.

Hệ thống có thể từ chối ảnh sai chắc chắn hoặc trả `NO_TRADE` khi ảnh quá cũ, hai ảnh lệch thời
điểm, OCR không xác minh được hoặc giá hiển thị lệch dữ liệu thị trường. Hãy chụp lại thay vì sửa
metadata để ép hệ thống tiếp tục.
