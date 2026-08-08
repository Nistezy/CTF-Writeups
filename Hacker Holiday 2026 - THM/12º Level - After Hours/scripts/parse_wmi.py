from pathlib import Path
import base64
import zlib
import struct
import sys

from dissect.cim import CIM


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE = Path(__file__).resolve().parent

INDEX = BASE / "INDEX.BTR"
OBJECTS = BASE / "OBJECTS.DATA"
MAP1 = BASE / "MAPPING1.MAP"
MAP2 = BASE / "MAPPING2.MAP"
MAP3 = BASE / "MAPPING3.MAP"

B64_OUT = BASE / "configdata.b64"
COMPRESSED_OUT = BASE / "payload_compressed.bin"
PAYLOAD_OUT = BASE / "payload.bin"
STRINGS_OUT = BASE / "payload_strings.txt"


# ============================================================
# UTILIDADES
# ============================================================

def check_files():
    files = [INDEX, OBJECTS, MAP1, MAP2, MAP3]

    print("[+] Verificando arquivos...")

    missing = []

    for f in files:
        if f.exists():
            print(f"    [OK] {f.name} ({f.stat().st_size:,} bytes)")
        else:
            print(f"    [!!] AUSENTE: {f}")
            missing.append(f)

    if missing:
        print("\n[!] Arquivos necessários não encontrados.")
        sys.exit(1)


def ascii_strings(data, minimum=5):
    """
    Extrai strings ASCII imprimíveis.
    """
    result = []
    current = bytearray()

    for byte in data:
        if 32 <= byte <= 126:
            current.append(byte)
        else:
            if len(current) >= minimum:
                try:
                    result.append(current.decode("ascii"))
                except UnicodeDecodeError:
                    pass

            current.clear()

    if len(current) >= minimum:
        try:
            result.append(current.decode("ascii"))
        except UnicodeDecodeError:
            pass

    return result


def utf16le_strings(data, minimum=5):
    """
    Extrai strings UTF-16LE simples.
    """
    result = []
    current = bytearray()

    i = 0

    while i + 1 < len(data):
        pair = data[i:i + 2]

        if 32 <= pair[0] <= 126 and pair[1] == 0:
            current.extend(pair)
        else:
            if len(current) >= minimum * 2:
                try:
                    result.append(current.decode("utf-16le"))
                except UnicodeDecodeError:
                    pass

            current.clear()

        i += 2

    if len(current) >= minimum * 2:
        try:
            result.append(current.decode("utf-16le"))
        except UnicodeDecodeError:
            pass

    return result


def inspect_pe(data):
    """
    Verifica se o payload possui cabeçalho PE.
    """
    print("\n" + "=" * 70)
    print("[+] ANÁLISE DO PAYLOAD")
    print("=" * 70)

    print("[+] Tamanho:", len(data), "bytes")
    print("[+] Primeiros 32 bytes:", data[:32].hex(" "))

    if data[:2] == b"MZ":
        print("[+] Header: MZ")
        print("[+] Parece ser um executável PE.")

        if len(data) >= 0x40:
            pe_offset = struct.unpack_from("<I", data, 0x3C)[0]

            print(f"[+] PE header offset: 0x{pe_offset:X}")

            if pe_offset + 4 <= len(data):
                signature = data[pe_offset:pe_offset + 4]

                print("[+] PE signature:", signature)

                if signature == b"PE\x00\x00":
                    print("[+] PE válido detectado.")

                    # COFF header
                    if pe_offset + 24 <= len(data):
                        machine = struct.unpack_from(
                            "<H",
                            data,
                            pe_offset + 4
                        )[0]

                        sections = struct.unpack_from(
                            "<H",
                            data,
                            pe_offset + 6
                        )[0]

                        print(f"[+] Machine: 0x{machine:04X}")
                        print(f"[+] Sections: {sections}")

                        # Optional header
                        optional_offset = pe_offset + 24

                        if optional_offset + 2 <= len(data):
                            magic = struct.unpack_from(
                                "<H",
                                data,
                                optional_offset
                            )[0]

                            print(
                                f"[+] Optional Header Magic: "
                                f"0x{magic:04X}"
                            )

                            if magic == 0x10B:
                                print("[+] PE32")

                            elif magic == 0x20B:
                                print("[+] PE32+")

    else:
        print("[!] Payload não começa com MZ.")

        # Verificação básica de assembly .NET
        if b"BSJB" in data:
            print("[+] Assinatura CLR/metadata 'BSJB' encontrada.")
            print("[+] Forte indicação de assembly .NET.")

        else:
            print(
                "[*] Não foi possível confirmar PE/.NET "
                "apenas pelo header."
            )


# ============================================================
# ABRIR WMI
# ============================================================

def open_repository():
    print("\n" + "=" * 70)
    print("[+] ABRINDO REPOSITÓRIO WMI")
    print("=" * 70)

    repo = CIM(
        INDEX.open("rb"),
        OBJECTS.open("rb"),
        [
            MAP1.open("rb"),
            MAP2.open("rb"),
            MAP3.open("rb"),
        ],
    )

    print("[+] WMI repository aberto.")

    return repo


# ============================================================
# ENCONTRAR CONFIGDATA
# ============================================================

def find_configdata(repo):

    print("\n" + "=" * 70)
    print("[+] PROCURANDO Win32_HardwareTelemetry")
    print("=" * 70)

    found = False
    configdata = None

    for namespace in repo.root.namespaces:

        namespace_name = str(namespace)

        if namespace_name.lower() != "<namespace root\\cimv2>":
            continue

        print("[+] Namespace:", namespace_name)

        for cls in namespace.classes:

            if cls.name != "Win32_HardwareTelemetry":
                continue

            found = True

            print("[+] Classe encontrada:", cls.name)

            print("[+] Instances:", len(list(cls.instances)))

            print("\n[+] Propriedades:")

            for name in cls.properties:
                print("    -", name)

            if "ConfigData" not in cls.properties:
                print("\n[!] ConfigData não encontrada.")
                continue

            prop = cls.properties["ConfigData"]

            print("\n[+] ConfigData encontrada.")

            try:
                configdata = prop.default_value
            except Exception as e:
                print("[!] Erro lendo default_value:", e)
                return None

            if not configdata:
                print("[!] ConfigData está vazia.")
                return None

            print("[+] Tipo:", type(configdata))
            print("[+] Tamanho:", len(configdata), "caracteres")

            return configdata

    if not found:
        print("[!] Win32_HardwareTelemetry não encontrada.")

    return None


# ============================================================
# BASE64
# ============================================================

def decode_base64(configdata):

    print("\n" + "=" * 70)
    print("[+] DECODIFICANDO BASE64")
    print("=" * 70)

    configdata = configdata.strip()

    B64_OUT.write_text(
        configdata,
        encoding="ascii"
    )

    print("[+] Salvo:", B64_OUT.name)
    print("[+] Base64 chars:", len(configdata))

    try:
        decoded = base64.b64decode(
            configdata,
            validate=True
        )

    except Exception as e:
        print("[!] Base64 inválido:", e)
        sys.exit(1)

    print("[+] Decoded bytes:", len(decoded))
    print("[+] Header:", decoded[:32].hex(" "))

    COMPRESSED_OUT.write_bytes(decoded)

    print("[+] Salvo:", COMPRESSED_OUT.name)

    return decoded


# ============================================================
# DEFLATE
# ============================================================

def decompress_payload(compressed):

    print("\n" + "=" * 70)
    print("[+] DESCOMPRIMINDO DEFLATE")
    print("=" * 70)

    payload = None

    # Primeiro tenta zlib normal
    try:
        print("[+] Tentando zlib...")
        payload = zlib.decompress(compressed)
        print("[+] zlib OK.")

    except zlib.error as e:

        print("[*] zlib falhou:", e)

        # Depois tenta raw DEFLATE
        try:
            print("[+] Tentando raw DEFLATE...")

            payload = zlib.decompress(
                compressed,
                -zlib.MAX_WBITS
            )

            print("[+] raw DEFLATE OK.")

        except zlib.error as e2:
            print("[!] raw DEFLATE também falhou:", e2)
            sys.exit(1)

    PAYLOAD_OUT.write_bytes(payload)

    print("[+] Payload descomprimido:", len(payload), "bytes")
    print("[+] Salvo:", PAYLOAD_OUT.name)

    return payload


# ============================================================
# STRINGS
# ============================================================

def extract_strings(data):

    print("\n" + "=" * 70)
    print("[+] EXTRAINDO STRINGS")
    print("=" * 70)

    ascii_result = ascii_strings(data)
    utf16_result = utf16le_strings(data)

    print("[+] ASCII strings:", len(ascii_result))
    print("[+] UTF-16LE strings:", len(utf16_result))

    with STRINGS_OUT.open(
        "w",
        encoding="utf-8",
        errors="replace"
    ) as f:

        f.write("========== ASCII ==========\n\n")

        for s in ascii_result:
            f.write(s + "\n")

        f.write("\n\n")
        f.write("========== UTF-16LE ==========\n\n")

        for s in utf16_result:
            f.write(s + "\n")

    print("[+] Strings salvas em:", STRINGS_OUT.name)

    # Mostrar strings potencialmente interessantes
    keywords = [
        "http",
        "https",
        "powershell",
        "cmd",
        "flag",
        "ctf",
        "token",
        "key",
        "secret",
        "password",
        "user",
        "admin",
        "telemetry",
        "socket",
        "connect",
        "assembly",
        "invoke",
    ]

    interesting = []

    for s in ascii_result + utf16_result:

        lower = s.lower()

        if any(keyword in lower for keyword in keywords):
            interesting.append(s)

    print("\n[+] Strings potencialmente interessantes:")

    if interesting:
        for s in interesting:
            print("    ", s)

    else:
        print("    Nenhuma encontrada.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(" WMI FORENSICS - EngineTelemetry")
    print("=" * 70)

    check_files()

    repo = open_repository()

    configdata = find_configdata(repo)

    if not configdata:
        print("\n[!] Não foi possível recuperar ConfigData.")
        sys.exit(1)

    compressed = decode_base64(configdata)

    payload = decompress_payload(compressed)

    inspect_pe(payload)

    extract_strings(payload)

    print("\n" + "=" * 70)
    print("[+] CONCLUÍDO")
    print("=" * 70)

    print("[+] Arquivos gerados:")
    print("    ", B64_OUT.name)
    print("    ", COMPRESSED_OUT.name)
    print("    ", PAYLOAD_OUT.name)
    print("    ", STRINGS_OUT.name)

    print("\n[!] O payload NÃO foi executado.")


if __name__ == "__main__":
    main()