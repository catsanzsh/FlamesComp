# decoder.py
from dataclasses import dataclass

@dataclass
class DecodedInstr:
    type: str      # e.g., 'arith', 'imm', 'load', 'store', 'branch', 'jump', etc.
    args: tuple    # operands or parameters specific to the type

def decode_instruction(word: int, pc: int) -> DecodedInstr:
    """Decode a 32-bit MIPS instruction word into a DecodedInstr object."""
    op = (word >> 26) & 0x3F  # top 6 bits: primary opcode
    if op == 0:  
        # R-type instruction (opcode 0). Funct field determines operation.
        rs    = (word >> 21) & 0x1F
        rt    = (word >> 16) & 0x1F
        rd    = (word >> 11) & 0x1F
        shamt = (word >> 6) & 0x1F
        funct = word & 0x3F
        # Map funct to operation type
        if funct in (0x20, 0x21):  # ADD or ADDU (treat both as ADD without overflow trap)
            return DecodedInstr('arith', ('ADD', rd, rs, rt))
        elif funct in (0x22, 0x23):  # SUB or SUBU
            return DecodedInstr('arith', ('SUB', rd, rs, rt))
        elif funct == 0x24:  # AND
            return DecodedInstr('arith', ('AND', rd, rs, rt))
        elif funct == 0x25:  # OR
            return DecodedInstr('arith', ('OR', rd, rs, rt))
        elif funct == 0x26:  # XOR
            return DecodedInstr('arith', ('XOR', rd, rs, rt))
        elif funct == 0x27:  # NOR
            return DecodedInstr('arith', ('NOR', rd, rs, rt))
        elif funct == 0x2A:  # SLT (set less than, signed)
            return DecodedInstr('arith', ('SLT', rd, rs, rt))
        elif funct == 0x2B:  # SLTU (set less than, unsigned)
            return DecodedInstr('arith', ('SLTU', rd, rs, rt))
        elif funct == 0x00:  # SLL (shift left logical)
            # SLL with all zero operands is NOP in MIPS
            if rs == 0 and rt == 0 and rd == 0 and shamt == 0:
                return DecodedInstr('nop', ())
            return DecodedInstr('shift', ('SLL', rd, rt, shamt))
        elif funct == 0x02:  # SRL (shift right logical)
            return DecodedInstr('shift', ('SRL', rd, rt, shamt))
        elif funct == 0x03:  # SRA (shift right arithmetic)
            return DecodedInstr('shift', ('SRA', rd, rt, shamt))
        elif funct == 0x08:  # JR (jump register)
            return DecodedInstr('jr', (rs,))  # usually rs = 31 for return
        elif funct == 0x09:  # JALR (jump and link register)
            # rd gets return address, jump to rs
            return DecodedInstr('jalr', (rd, rs))
        elif funct == 0x10:  # MFHI (move from HI register)
            return DecodedInstr('mfhi', (rd,))
        elif funct == 0x12:  # MFLO (move from LO register)
            return DecodedInstr('mflo', (rd,))
        elif funct == 0x11:  # MTHI (move to HI)
            return DecodedInstr('mthi', (rs,))
        elif funct == 0x13:  # MTLO (move to LO)
            return DecodedInstr('mtlo', (rs,))
        elif funct == 0x18:  # MULT (signed multiply)
            return DecodedInstr('mult', (rs, rt))
        elif funct == 0x19:  # MULTU (unsigned multiply)
            return DecodedInstr('multu', (rs, rt))
        elif funct == 0x1A:  # DIV (signed divide)
            return DecodedInstr('div', (rs, rt))
        elif funct == 0x1B:  # DIVU (unsigned divide)
            return DecodedInstr('divu', (rs, rt))
        else:
            return DecodedInstr('unknown', ('SPECIAL', funct, rs, rt, rd, shamt))
    elif op == 0x02 or op == 0x03:
        # J-type: J (0x02) or JAL (0x03)
        target = word & 0x03FFFFFF
        # The jump target is formed by (PC & 0xF0000000) | (target << 2)
        target_addr = ((pc + 4) & 0xF0000000) | (target << 2)
        if op == 0x02:
            return DecodedInstr('jump', (target_addr, False))   # Jump (no link)
        else:
            return DecodedInstr('jump', (target_addr, True))    # Jump and Link
    else:
        # I-type instructions
        rs  = (word >> 21) & 0x1F
        rt  = (word >> 16) & 0x1F
        imm = word & 0xFFFF
        # Sign-extend the immediate for operations where needed
        imm_signed = imm if imm < 0x8000 else imm - 0x10000
        if op == 0x04:  # BEQ
            target_addr = pc + 4 + (imm_signed << 2)
            return DecodedInstr('branch', ('BEQ', rs, rt, target_addr))
        elif op == 0x05:  # BNE
            target_addr = pc + 4 + (imm_signed << 2)
            return DecodedInstr('branch', ('BNE', rs, rt, target_addr))
        elif op == 0x06:  # BLEZ (branch if <= 0)
            target_addr = pc + 4 + (imm_signed << 2)
            return DecodedInstr('branch', ('BLEZ', rs, None, target_addr))
        elif op == 0x07:  # BGTZ (branch if > 0)
            target_addr = pc + 4 + (imm_signed << 2)
            return DecodedInstr('branch', ('BGTZ', rs, None, target_addr))
        elif op == 0x08 or op == 0x09:  # ADDI, ADDIU
            # (We treat both as ADD immediate, ignoring overflow trapping of ADDI)
            return DecodedInstr('imm', ('ADD', rt, rs, imm_signed))
        elif op == 0x0A or op == 0x0B:  # SLTI, SLTIU
            cmp_type = 'SLT' if op == 0x0A else 'SLTU'
            return DecodedInstr('imm', (cmp_type, rt, rs, imm_signed))
        elif op == 0x0C:  # ANDI (logical AND immediate, zero-extended imm)
            return DecodedInstr('imm', ('AND', rt, rs, imm))
        elif op == 0x0D:  # ORI
            return DecodedInstr('imm', ('OR', rt, rs, imm))
        elif op == 0x0E:  # XORI
            return DecodedInstr('imm', ('XOR', rt, rs, imm))
        elif op == 0x0F:  # LUI (load upper immediate)
            # LUI loads imm << 16 into rt
            return DecodedInstr('lui', (rt, imm))
        elif op == 0x20:  # LB (load byte, sign-extended)
            return DecodedInstr('load', ('BYTE_S', rt, rs, imm_signed))
        elif op == 0x24:  # LBU (load byte unsigned)
            return DecodedInstr('load', ('BYTE_U', rt, rs, imm_signed))
        elif op == 0x21:  # LH (load halfword, sign-extended)
            return DecodedInstr('load', ('HALF_S', rt, rs, imm_signed))
        elif op == 0x25:  # LHU (load halfword unsigned)
            return DecodedInstr('load', ('HALF_U', rt, rs, imm_signed))
        elif op == 0x23:  # LW (load word)
            return DecodedInstr('load', ('WORD', rt, rs, imm_signed))
        elif op == 0x28:  # SB (store byte)
            return DecodedInstr('store', ('BYTE', rt, rs, imm_signed))
        elif op == 0x29:  # SH (store halfword)
            return DecodedInstr('store', ('HALF', rt, rs, imm_signed))
        elif op == 0x2B:  # SW (store word)
            return DecodedInstr('store', ('WORD', rt, rs, imm_signed))
        else:
            # Unhandled opcode
            return DecodedInstr('unknown', ('OP', op, rs, rt, imm_signed))
