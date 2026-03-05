
from Configuration_data import ConfigurationDataScenario, PathArquivoDados
import os
from create_dat_files import CreatorDatFiles

# Diretório base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, "Dados")
PASTAS = {
    'todos_municipios': os.path.join(DADOS_DIR, "Dados_todos_municipios"),
    'lagoa_santa': os.path.join(DADOS_DIR, "Dados Lagoa Santa/dados_brutos")
}   

if __name__ == "__main__":
    municipio = "Lagoa Santa"
    configs = ConfigurationDataScenario(
        municipio = municipio,
        budget = 164300000,
        I_L1 = 3818078,
        raios_criticos = {
            "PHC": 5000,
            "SHC": 30000,
            "THC": 35000
        },
        custos_mensais_PHC = {"eSF": 1455500, "eSB": 640420, "eMulti": 640420 },
        custos_mensais_SHC = {"EQ2": 0},
        custos_mensais_THC = {"EQ3": 0},
        equipes_saude_primario = ["eSF", "eSB", "eMulti"],
        equipes_saude_secundario = ["EQ2"],
        equipes_saude_terciario = ["EQ3"],
        name_output_file = "Lagoa_Santa",
        maximo_de_unidades_abertas = {"1": 10, "2": 1, "3": 1},
        encaminhamentos_primeiro_nivel = {"1": 0.71, "2": 0.20, "3": 0.05},
        encaminhamentos_segundo_nivel = {"1": 0.65, "2": 0.20, "3": 0.10},
        encaminhamentos_terceiro_nivel = {"1": 0.8, "2": 0.1, "3": 0.05},
        maximo_atendimentos_telemedicina = {"MAX_TELE_PHC": 0.05, "MAX_TELE_SHC": 0.05,"MAX_TELE_THC": 0.05},
        maximo_deslocamento = {"MAX_HOME_PHC": 1, "MAX_HOME_SHC": 0.15, "MAX_HOME_THC": 0.05,},
        name_output_file_distancias = "Dist_Lagoa_Santa"


    )

    paths_arquivos = PathArquivoDados(
        path_arquivo_setores_censitarios=os.path.join(PASTAS['lagoa_santa'], "dados_setor_censitario_LAGOA_SANTA.xlsx"),
        path_dados_IVS=os.path.join(PASTAS['todos_municipios'], "dados_IVS.xlsx"),
        path_equipes_PHC=os.path.join(PASTAS['lagoa_santa'], "v02_Equipe.xlsx"),
        path_setores_com_UBS=os.path.join(PASTAS['todos_municipios'], "setores_com_ubs.xlsx"),
        path_json_distances = os.path.join(PASTAS['lagoa_santa'], "lagoa_santa_distance_test.json"),
        path_arquivos_dat_final = os.path.join(PASTAS['lagoa_santa']),
    )


    creator = CreatorDatFiles(configuration_data=configs, path_arquivos_data=paths_arquivos, create_distance_file=True)
    creator.create_file()


