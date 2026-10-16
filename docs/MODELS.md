# Models and licences

Nothing has been downloaded by this repo. Sizes below are rough ESTIMATES (params x ~0.6 bytes for Q4_K_M), not measured; check the
actual file size on the download page before fetching.

## Licences

Checked against the model cards on **17 Oct 2026** (check reported by Benedict from an earlier assistant check; the cloud sandbox used to
build this repo cannot reach Hugging Face, so it was **not re-checked here**). Re-confirm on the cards before the poster is printed.

| Tier | Model | Params | Licence | Model card (source of the licence) |
|---|---|---|---|---|
| small | Qwen2.5-1.5B-Instruct | 1.5B | Apache-2.0 | https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct |
| mid | Phi-3.5-mini-instruct | 3.8B | MIT | https://huggingface.co/microsoft/Phi-3.5-mini-instruct |
| large | Qwen2.5-7B-Instruct | 7.6B | Apache-2.0 | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct |

- **llama.cpp**: MIT, per its GitHub page (https://github.com/ggml-org/llama.cpp), same check date and caveat.
- **Not checked:** the licence of the *GGUF conversion repositories* you actually download from (for example `Qwen/Qwen2.5-1.5B-Instruct-GGUF`,
  `bartowski/Phi-3.5-mini-instruct-GGUF`). Conversions normally carry the base model's licence, but read each repo's card too.
- Python libraries used (`psutil`, `matplotlib`, `pytest`, optional `pyserial`, optional `paho-mqtt`) have not had their licences recorded here.
- N-ATLAS is not used. Qwen2.5-3B is avoided on purpose (its licence is not the permissive one the other Qwen2.5 sizes use; not re-checked).

## Files and sizes

| Tier | Expected file in `models/` | Est. size | Download repo used in the code catalogue |
|---|---|---|---|
| small | `qwen2.5-1.5b-instruct-Q4_K_M.gguf` | ~0.9 GB | `Qwen/Qwen2.5-1.5B-Instruct-GGUF` |
| mid | `phi-3.5-mini-instruct-Q4_K_M.gguf` | ~2.3 GB | `bartowski/Phi-3.5-mini-instruct-GGUF` |
| large | `qwen2.5-7b-instruct-Q4_K_M.gguf` | ~4.6 GB | `Qwen/Qwen2.5-7B-Instruct-GGUF` |

Also needed: a CPU `llama-server` binary from the llama.cpp releases at `bin/llama-server` (or set `LLAMA_SERVER`, or pass `--llama-server`).
