# DAPI — Dynamic API

DAPI (Dynamic API) is a minimalist, self-reflective, type-safe computation system. It allows logic to be defined, transformed, and executed through a unified structure of typed operators and transactions.

DAPI is designed for human–AI collaboration, self-modifying architectures, and as a substrate for reflective logic.

---

## 🔍 What is DAPI?

- Everything is an **operator**.
- Every execution is a **transaction**.
- All memory flows through **assignments** in a shared `scope`.

You don’t call code — you describe how it should behave, where data should go, and DAPI interprets it.

---

## 🧠 Why DAPI?

- **Self-definition**: DAPI defines itself through its own language.
- **Live reflection**: Create and invoke operators that build or destroy others.
- **Composability**: Functions are transaction chains.
- **Type safety**: Uses JSON Schema as a base for input/output types.
- **Execution minimalism**: create → assign → invoke → forget.

---

## 📦 Key Concepts

- `create_type(name, schema)`
- `create_operator(name, input_type, output_type, code)`
- `create_transaction(operator)`
- `create_assignment(transaction_id, from, to)`
- `create_scope(name, tx_ids, interpreter, scope)`

---

## 📘 Documentation

See full spec:  
→ [`DAPI_Specification_updated.md`](DAPI_Specification_updated.md)

---

## 📝 License

This project is licensed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

You are free to:
- Use, share, and modify the contents of this repository.
- Integrate DAPI into other systems, including commercial applications.

**Under the following conditions:**
- You must give appropriate credit to **Alexander Podgorny**.
- You must retain the name **DAPI** (Dynamic API) when referencing the architecture, logic, or model.

📄 [Full License Text](LICENSE_DAPI_CC_BY_4.0.txt)  
🔗 https://creativecommons.org/licenses/by/4.0/
