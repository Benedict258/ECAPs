# Models

Nothing has been downloaded. Sizes below are rough ESTIMATES (params x ~0.6 bytes for Q4_K_M), not measured; check the
actual file size on the download page before fetching. Licences are from memory and **UNVERIFIED** (the build sandbox could
not reach Hugging Face): confirm each model card before use.

| Tier | Model | Params | Expected file in `models/` | Est. size | Licence (verify) |
|---|---|---|---|---|---|
| small | Qwen2.5-1.5B-Instruct | 1.5B | `qwen2.5-1.5b-instruct-Q4_K_M.gguf` | ~1 GB | Apache-2.0 |
| mid | Phi-3.5-mini-instruct | 3.8B | `phi-3.5-mini-instruct-Q4_K_M.gguf` | ~2.3 GB | MIT |
| large | Qwen2.5-7B-Instruct | 7.6B | `qwen2.5-7b-instruct-Q4_K_M.gguf` | ~4.7 GB | Apache-2.0 |

Also needed: a CPU `llama-server` binary from llama.cpp releases (MIT) at `bin/llama-server` (or set `LLAMA_SERVER`).
N-ATLAS is not used. Qwen2.5-3B is avoided because of its non-permissive licence.
