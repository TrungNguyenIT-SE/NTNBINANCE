# Stage L dependency and license audit

> Audit date: `16/11/2026` (Asia/Saigon)
>
> Result: **PASS**

| Check | Result |
|---|---|
| Package/version | `Pillow==13.0.0` |
| Source | PyPI project maintained by python-pillow/Pillow |
| Interpreter/platform | CPython 3.14, Windows x86-64 wheel available and installed |
| Installed license expression | `MIT-CMU` |
| Installed license file | `pillow-13.0.0.dist-info/licenses/LICENSE` |
| Added transitive Python packages | None |
| Decoder features exercised | JPEG `true`, WebP `true`, zlib/PNG `true` |
| `pip check` | No broken requirements |
| Paid key/service/account | None |

Primary references:

- <https://pypi.org/project/pillow/13.0.0/>
- <https://pillow.readthedocs.io/en/stable/handbook/security.html>
- <https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html>

The library is used only for local decode/verify/re-encode. Stage L follows the upstream guidance to
pin the package, handle decompression-bomb signals and explicitly avoid copying EXIF/XMP/ICC metadata.
No commercial license, cloud decoder or SaaS scanner was introduced. New cash cost is **0 VNĐ**.
