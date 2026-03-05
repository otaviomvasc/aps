from dataclasses import dataclass
from re import S

@dataclass
class ConfigurationDataScenario:
    municipio: str
    budget: float or int
    I_L1: float or int # O que é isso ?
    raios_criticos: dict
    custos_mensais_PHC:dict
    custos_mensais_SHC:dict
    custos_mensais_THC:dict
    equipes_saude_primario: list
    equipes_saude_secundario: list
    equipes_saude_terciario: list
    name_output_file:str
    maximo_de_unidades_abertas: dict
    encaminhamentos_primeiro_nivel:dict
    encaminhamentos_segundo_nivel:dict
    encaminhamentos_terceiro_nivel:dict
    maximo_atendimentos_telemedicina:dict
    maximo_deslocamento: dict
    name_output_file_distancias: str


@dataclass
class PathArquivoDados:
    path_arquivo_setores_censitarios:str
    path_dados_IVS:str
    path_equipes_PHC:str
    path_setores_com_UBS:str
    path_json_distances:str = None
    path_arquivos_dat_final:str = None