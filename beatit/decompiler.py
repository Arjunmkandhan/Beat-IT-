"""Phase 7 inverse: Reverse-engineer a native Beat It executable into .bi source code.

This decompiler does NOT extract embedded source. Instead, it disassembles and
analyzes the native Windows machine code and PE data sections using objdump
and binary inspection to reconstruct the program logic into valid Beat It source.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from errors import BeatItError


def find_objdump() -> str | None:
    """Find objdump.exe on PATH or in standard MinGW installation directories."""
    path = shutil.which("objdump")
    if path:
        return path
    candidates = [
        r"C:\Program Files\CodeBlocks\MinGW\bin\objdump.exe",
        r"C:\MinGW\bin\objdump.exe",
        r"C:\msys64\mingw64\bin\objdump.exe",
        r"C:\msys64\ucrt64\bin\objdump.exe",
        r"C:\TDM-GCC-64\bin\objdump.exe",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c
    return None


def extract_sound_strings(data: bytes) -> list[str]:
    """Scan PE binary data sections (.rdata) for .wav sound paths."""
    matches = re.findall(b'([a-zA-Z0-9_/\\\\-]+\\.wav)', data)
    seen = set()
    result = []
    for m in matches:
        s = m.decode("utf-8", errors="ignore").replace("\\", "/")
        if s not in seen:
            seen.add(s)
            result.append(s)
    return result


def decompile_file(executable_file: str | Path, output_file: str | Path | None = None) -> Path:
    """Disassemble and reverse-engineer a native Beat It .exe back into a .bi file."""
    executable = Path(executable_file).resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)
    if executable.suffix.lower() != ".exe":
        raise BeatItError("Decompiler input must be a native Windows .exe file")

    data = executable.read_bytes()
    if not data.startswith(b"MZ"):
        raise BeatItError("File is not a valid Windows PE executable")

    # 1. Extract sound paths from binary data (.rdata section)
    sound_paths = extract_sound_strings(data)
    sound_map = {}   # "sound_0" -> "s.kick"
    modules = {}     # "sounds" -> "s"

    for idx, path_str in enumerate(sound_paths):
        parts = path_str.split("/")
        if len(parts) >= 2:
            module = parts[0]
            sound_name = Path(parts[-1]).stem
        else:
            module = "sounds"
            sound_name = Path(path_str).stem
        alias = module[0] if len(module) > 0 else "s"
        modules[module] = alias
        sound_map[f"sound_{idx}"] = f"{alias}.{sound_name}"

    # 2. Disassemble machine code with objdump
    objdump = find_objdump()
    disassembly = ""
    if objdump:
        try:
            res = subprocess.run(
                [objdump, "-d", "-M", "intel", str(executable)],
                capture_output=True,
                text=True,
                check=True
            )
            disassembly = res.stdout
        except Exception:
            disassembly = ""

    lines = []
    lines.append("// =================================================================")
    lines.append(f"// Decompiled from native Windows executable: {executable.name}")
    lines.append("// Reverse-engineered from machine code & data sections")
    lines.append("// =================================================================")
    lines.append("")

    # Imports
    for mod, alias in sorted(modules.items()):
        lines.append(f"import from {mod} as {alias}")
    lines.append("")

    # Extract disassembly lines for user functions (<fn_*>) and main (<main>)
    user_lines = []
    if disassembly:
        in_user_code = False
        for dline in disassembly.splitlines():
            header_match = re.match(r"^[0-9a-fA-F]+\s+<([^>]+)>:", dline.strip())
            if header_match:
                lbl = header_match.group(1)
                if lbl == "main" or lbl.startswith("fn_") or lbl.startswith("for_") or lbl.startswith("endfor_"):
                    in_user_code = True
                elif re.match(r"^(?:beatit_|__main|_setargv|__dyn_tls|_|WinMain|mainCRTStartup)", lbl):
                    in_user_code = False
                else:
                    in_user_code = False
            
            if in_user_code:
                user_lines.append(dline)

    if user_lines:
        assignments = []
        lists = {}
        curr_list = None
        rax_val = "0"
        rcx_val = "0"
        in_loop = False
        loop_var = "i"
        loop_target = None
        loop_body = []
        recovered_loops = []

        for line in user_lines:
            l = line.strip()
            if not l:
                continue

            # Loop boundaries
            if re.search(r"<for_\d+>:", l):
                in_loop = True
                continue
            if re.search(r"<endfor_\d+>:", l):
                if in_loop and loop_target:
                    recovered_loops.append((loop_var, loop_target, list(loop_body)))
                in_loop = False
                loop_body = []
                loop_target = None
                continue

            # mov rax, 0x...
            m_imm = re.search(r"mov\s+rax,\s*(0x[0-9a-fA-F]+|\d+)", l)
            if m_imm:
                val = m_imm.group(1)
                rax_val = str(int(val, 16) if val.startswith("0x") else int(val))

            # lea rax, [rip+...] # ... <sound_N>
            m_sound = re.search(r"lea\s+rax,.*<(sound_\d+)>", l)
            if m_sound:
                rax_val = sound_map.get(m_sound.group(1), m_sound.group(1))

            # mov rax, QWORD PTR [rip+...] # ... <var_NAME>
            m_vread = re.search(r"mov\s+rax,\s*QWORD PTR.*<var_([a-zA-Z0-9_]+)>", l)
            if m_vread:
                rax_val = m_vread.group(1)

            # mov QWORD PTR [rip+...], rax # ... <var_NAME>
            m_vwrite = re.search(r"mov\s+QWORD PTR.*,\s*rax.*<var_([a-zA-Z0-9_]+)>", l)
            if m_vwrite:
                v_name = m_vwrite.group(1)
                if in_loop:
                    loop_var = v_name
                else:
                    assignments.append((v_name, rax_val))

            # lea r8, [rip+...] # ... <list_NAME>
            m_list_ref = re.search(r"lea\s+r8,.*<list_([a-zA-Z0-9_]+)>", l)
            if m_list_ref:
                curr_list = m_list_ref.group(1)
                if in_loop:
                    loop_target = curr_list
                elif curr_list not in lists:
                    lists[curr_list] = []

            # Loop range limit check: cmp rax, <imm>
            m_cmp_imm = re.search(r"cmp\s+rax,\s*(0x[0-9a-fA-F]+|\d+)", l)
            if m_cmp_imm and in_loop and not loop_target:
                cval = m_cmp_imm.group(1)
                limit = int(cval, 16) if cval.startswith("0x") else int(cval)
                loop_target = f"range({limit})"

            # mov QWORD PTR [r8...], rax (writing into list)
            if not in_loop and re.search(r"mov\s+QWORD PTR\s*\[r8.*,\s*rax", l):
                if curr_list and curr_list in lists:
                    lists[curr_list].append(rax_val)

            # mov rcx, rax
            if re.search(r"mov\s+rcx,\s*rax", l):
                rcx_val = rax_val

            # mov rcx, 0x...
            m_rcx_imm = re.search(r"mov\s+rcx,\s*(0x[0-9a-fA-F]+|\d+)", l)
            if m_rcx_imm:
                val = m_rcx_imm.group(1)
                rcx_val = str(int(val, 16) if val.startswith("0x") else int(val))

            # call beatit_play
            if "call" in l and "beatit_play" in l:
                call_stmt = f"play({rcx_val})"
                if in_loop:
                    loop_body.append(call_stmt)
                else:
                    assignments.append((None, call_stmt))

            # call beatit_sleep
            if "call" in l and "beatit_sleep" in l:
                try:
                    ms = int(rcx_val)
                    if ms >= 1000 and ms % 1000 == 0:
                        sleep_stmt = f"sleep({ms // 1000}, s)"
                    else:
                        sleep_stmt = f"sleep({ms}, ms)"
                except ValueError:
                    sleep_stmt = f"sleep({rcx_val}, ms)"

                if in_loop:
                    loop_body.append(sleep_stmt)
                else:
                    assignments.append((None, sleep_stmt))

        # Output reconstructed assignments
        for var_name, val in assignments:
            if var_name is None:
                lines.append(val)
            else:
                lines.append(f"{var_name} = {val}")
        if assignments:
            lines.append("")

        # Output reconstructed lists
        for lname, items in lists.items():
            lines.append(f"{lname} = [{', '.join(items)}]")
            lines.append("")

        # Output reconstructed loops
        for lvar, ltarget, lbody in recovered_loops:
            lines.append(f"for {lvar} in {ltarget}:")
            for bstmt in lbody:
                lines.append(f"    {bstmt}")
            lines.append("")

    else:
        # Fallback if objdump disassembly is unavailable
        lines.append("// Note: Disassembler unavailable; reconstructed from PE asset tables")
        var_names = []
        for idx, (label, sound_ref) in enumerate(sound_map.items()):
            v = f"beat{idx + 1}"
            var_names.append(v)
            lines.append(f"{v} = {sound_ref}")
        lines.append("")
        if var_names:
            lines.append(f"order = [{', '.join(var_names)}]")
            lines.append("")
            lines.append("for i in order:")
            lines.append("    play(i)")

    output = Path(output_file) if output_file else executable.with_suffix(".bi")
    output = output.resolve().with_suffix(".bi")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return output