import pandas as pd


from Configuration_data import ConfigurationDataScenario, PathArquivoDados
from distance_API_calculator import DistanceAPICalculator


class ScenarioDataBuilder():
    def __init__(self, 
                configuration_data:ConfigurationDataScenario,
                path_arquivos_data: PathArquivoDados,
                create_distance_data:bool
                ) -> None:

        self.configuration_data = configuration_data
        self.path_arquivos_data = path_arquivos_data
        self.create_distance_data = create_distance_data



    def read_and_format_path_arquivo_setores_censitarios(self):
        df = pd.read_excel(self.path_arquivos_data.path_arquivo_setores_censitarios)
        df = df[df["MUNICIPIO"] == self.configuration_data.municipio]
        self.df_setor_censitario = df[["MUNICIPIO", "SETOR", "V01006", "LAT", "LONG"]].copy()

    
    def read_and_format_path_setores_com_UBS(self):
        df = pd.read_excel(self.path_arquivos_data.path_setores_com_UBS)
        self.df_setor_censitario = self.df_setor_censitario.merge(df, how="left", on="SETOR")
        self.df_setor_censitario["CO_UNIDADE_UBS"] = pd.to_numeric(
    self.df_setor_censitario["CO_UNIDADE_UBS"],
    errors="coerce"
)

    def read_and_format_dados_IVS(self):
        df = pd.read_excel(self.path_arquivos_data.path_dados_IVS)
        self.df_setor_censitario = self.df_setor_censitario.merge(df[['SETOR', 'Capital Humano', 'Infra Urbana','Vulnerab. Saúde', 'Índice']],
         how="left", on="SETOR")


    def read_and_format_path_equipes_PHC(self):
        dict_municipio_CODIGO = {"Lagoa Santa": 313760, "Belo Horizonte": 310620, "Contagem": 311860, "DIVINOPOLIS": 312230, "Montes Claros": 314330}
        df = pd.read_excel(self.path_arquivos_data.path_equipes_PHC)
        df = df[df.CO_MUNICIPIO_GESTOR == dict_municipio_CODIGO[self.configuration_data.municipio]][["CO_UNIDADE", "TP_EQUIPE"]].reset_index(drop=True) #TODO: USAR O MUNICIPIO GESTOR SEM HARDCODE
        df_pivot = (
                    df
                    .groupby(["CO_UNIDADE", "TP_EQUIPE"])
                    .size()
                    .unstack(fill_value=0)
                    .reset_index()
                )

        self.df_setor_censitario = self.df_setor_censitario.merge(df_pivot, how="left", left_on="CO_UNIDADE_UBS", right_on = "CO_UNIDADE")
        


    def build(self):
        self.read_and_format_path_arquivo_setores_censitarios()
        self.read_and_format_path_setores_com_UBS()
        self.read_and_format_dados_IVS()
        self.read_and_format_path_equipes_PHC()
        path_d = f"dados_{self.configuration_data.municipio}.xlsx"
        self.df_setor_censitario.to_excel(path_d)
        dist_PHC_SC = None
        dist_SC_SC = None
        if self.create_distance_data:
            instance_data_creator = DistanceAPICalculator(
                                                        self.path_arquivos_data.path_json_distances,
                                                        self.df_setor_censitario,  )
            dist_PHC_SC, dist_SC_SC =  instance_data_creator.build()                                       
        return {"dfs": self.df_setor_censitario, "configurations": self.configuration_data, "create_distance_data": self.create_distance_data,
                "dist_PHC_SC": dist_PHC_SC, "dist_SC_SC": dist_SC_SC}
