/* ----- 1: Chuẩn hóa chuỗi -----
   Đưa chuỗi về dạng sạch: chữ thường, bỏ dấu câu, gộp khoảng trắng. */
function chuanHoa(s) {
  return (s || "")
    .toLowerCase()
    .trim()
    .replace(/[.,!?;:"'’”“]/g, "")  // bỏ dấu câu
    .replace(/\s+/g, " ");           // gộp nhiều khoảng trắng thừa
}

/* ----- 2: Khoảng cách Levenshtein -----
   Số thao tác tối thiểu (thêm / xóa / thay 1 ký tự) để biến a thành b. */
function levenshtein(a, b) {
  const m = a.length, n = b.length;
  const d = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) d[i][0] = i;
  for (let j = 0; j <= n; j++) d[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      d[i][j] = Math.min(
        d[i - 1][j] + 1,       // xóa
        d[i][j - 1] + 1,       // thêm
        d[i - 1][j - 1] + cost // thay thế (cost = 0 nếu trùng ký tự)
      );
    }
  }
  return d[m][n];
}

/* ----- 3: Độ giống nhau (0 = khác hẳn, 1 = trùng khít) ----- */
function doTuongDong(a, b) {
  a = chuanHoa(a);
  b = chuanHoa(b);
  if (a === b) return 1;
  const maxLen = Math.max(a.length, b.length);
  if (maxLen === 0) return 1;
  return 1 - levenshtein(a, b) / maxLen;
}

/* -----  4: Hàm chính -----
   So text nhận dạng với TỪNG đáp án chấp nhận, lấy kết quả giống nhất.
   - textNhanDang: chuỗi trả về từ Web Speech API
   - cauHoi: 1 phần tử trong mảng questions của metadata.json
   - nguong: ngưỡng đúng (mặc định lấy từ metadata.json, vd 0.8) */
function kiemTraDapAn(textNhanDang, cauHoi, nguong = 0.8) {
  const dsDapAn = (cauHoi.acceptedAnswers && cauHoi.acceptedAnswers.length)
    ? cauHoi.acceptedAnswers
    : [cauHoi.keyword];

  let doGiongCaoNhat = 0;
  let dapAnKhopNhat = "";

  for (const dapAn of dsDapAn) {
    const d = doTuongDong(textNhanDang, dapAn);
    if (d > doGiongCaoNhat) {
      doGiongCaoNhat = d;
      dapAnKhopNhat = dapAn;
    }
  }

  return {
    dung: doGiongCaoNhat >= nguong,                 // true / false
    doGiong: Math.round(doGiongCaoNhat * 100) / 100, // vd 0.86
    dapAnKhopNhat: dapAnKhopNhat,                     // đáp án giống nhất
    textNhanDang: chuanHoa(textNhanDang)             // text đã chuẩn hóa (để debug/log)
  };
}
