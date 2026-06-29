import os
import pandas as pd


BASE_DIR = r"C:\Users\user\Documents\Workspace\campanha_2026\alagoas-political-intelligence"

ARQUIVO_PARCEIROS_CSV = os.path.join(
    BASE_DIR,
    "data",
    "reference",
    "parceiros_davi_2026.csv",
)

ARQUIVO_PARCEIROS_XLSX = os.path.join(
    BASE_DIR,
    "data",
    "reference",
    "parceiros_davi_2026.xlsx",
)

DIR_IMAGENS = os.path.join(
    BASE_DIR,
    "dashboard_mobile_parceiros",
    "assets",
    "parceiros",
)


def encontrar_arquivo(prefixos):
    if not os.path.exists(DIR_IMAGENS):
        raise FileNotFoundError(f"Pasta não encontrada: {DIR_IMAGENS}")

    arquivos = os.listdir(DIR_IMAGENS)

    for arquivo in arquivos:
        nome_lower = arquivo.lower()

        for prefixo in prefixos:
            if nome_lower.startswith(prefixo.lower()):
                caminho_relativo = os.path.join(
                    "assets",
                    "parceiros",
                    arquivo,
                )
                return caminho_relativo.replace("\\", "/")

    return ""


def main():
    print("=" * 80)
    print("ATUALIZANDO IMAGENS DOS PARCEIROS — DAVI 2026")
    print("=" * 80)

    if not os.path.exists(ARQUIVO_PARCEIROS_CSV):
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_PARCEIROS_CSV}")

    print("Arquivos encontrados na pasta de imagens:")
    for arquivo in os.listdir(DIR_IMAGENS):
        print(f"- {arquivo}")

    foto_gabi = encontrar_arquivo(["foto-gabi", "gabi-foto", "gabi"])
    logo_gabi = encontrar_arquivo(["logo-gabi-2026", "logo-gabi", "gabi-logo"])

    print()
    print(f"Foto Gabi localizada: {foto_gabi or 'NÃO ENCONTRADA'}")
    print(f"Logo Gabi localizada: {logo_gabi or 'NÃO ENCONTRADA'}")

    df = pd.read_csv(
        ARQUIVO_PARCEIROS_CSV,
        sep=",",
        encoding="utf-8-sig",
        dtype=str,
    ).fillna("")

    if "foto_parceiro" not in df.columns:
        df["foto_parceiro"] = ""

    if "logo_parceiro" not in df.columns:
        df["logo_parceiro"] = ""

    mascara_gabi = (
        df["id_parceiro"].astype(str).str.lower().str.strip().eq("gabi-goncalves")
        | df["nome_parceiro"].astype(str).str.upper().str.contains("GABI", na=False)
    )

    if not mascara_gabi.any():
        raise ValueError("Não encontrei a linha da Gabi Gonçalves em parceiros_davi_2026.csv.")

    if foto_gabi:
        df.loc[mascara_gabi, "foto_parceiro"] = foto_gabi

    if logo_gabi:
        df.loc[mascara_gabi, "logo_parceiro"] = logo_gabi

    df.to_csv(
        ARQUIVO_PARCEIROS_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    df.to_excel(
        ARQUIVO_PARCEIROS_XLSX,
        index=False,
    )

    print()
    print("Tabela de parceiros atualizada com sucesso:")
    print(ARQUIVO_PARCEIROS_CSV)
    print(ARQUIVO_PARCEIROS_XLSX)

    print()
    print("Linha atualizada da Gabi:")
    print(df.loc[mascara_gabi, ["id_parceiro", "nome_parceiro", "foto_parceiro", "logo_parceiro"]])

    print("=" * 80)


if __name__ == "__main__":
    main()