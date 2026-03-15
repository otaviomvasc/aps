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
        #df = pd.read_excel(self.path_arquivos_data.path_arquivo_setores_censitarios)
        df = pd.read_excel(r"C:\aps\GeraDadosAPS\Dados\Lagoa Santa\dados_brutos\dados_setor_censitario_LAGOA_SANTA.xlsx")
        if df.MUNICIPIO.iloc[0] == 'Divinópolis':
            df = df[df["MUNICIPIO"] == 'Divinópolis'] 
        else:
            df = df[df["MUNICIPIO"] == self.configuration_data.municipio]
        df["V01006"] = df["V01006"].apply(lambda x: 0 if isinstance(x, str) else x)
        self.df_setor_censitario = df[["MUNICIPIO", "SETOR", "V01006", "LAT", "LONG"]].copy()

    
    def read_and_format_path_setores_com_UBS(self):
        df = pd.read_excel(self.path_arquivos_data.path_setores_com_UBS)
        self.df_setor_censitario = self.df_setor_censitario.merge(df, how="left", on="SETOR")
        self.df_setor_censitario["CO_UNIDADE_UBS"] = pd.to_numeric(
        self.df_setor_censitario["CO_UNIDADE_UBS"],
    errors="coerce"
        )       
        self.df_setor_censitario["CO_UNIDADE_UBS"] = self.df_setor_censitario["CO_UNIDADE_UBS"].fillna(0)

    def read_and_format_dados_IVS(self):
        df = pd.read_excel(self.path_arquivos_data.path_dados_IVS)
        self.df_setor_censitario = self.df_setor_censitario.merge(df[['SETOR', 'Capital Humano', 'Infra Urbana','Vulnerab. Saúde', 'Índice']],
         how="left", on="SETOR")


    def read_and_format_path_equipes_PHC(self):
        dict_municipio_CODIGO = {"Lagoa Santa": 313760, "Belo Horizonte": 310620, "Contagem": 311860, "Divinopolis": 312230, "Montes Claros": 314330}
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
        
    def read_and_format_SC_to_cluster_data(self):
        self.df_cluster = pd.read_csv(self.path_arquivos_data.path_cluster_CSV)


    def merge_cluster_in_SC_data(self):
        self.df_setor_censitario = self.df_setor_censitario.merge(self.df_cluster, how="left", right_on="CD_SETOR", left_on="SETOR")

    def agg_populacao_por_cluster(self):
        """
        Premissa de agregacao da populacao:
        Somar a populacao de todos os setores do cluster
        """
        df_agg_pop = self.df_setor_censitario.groupby(by="cluster").agg({"V01006": "sum"}).reset_index()
        return df_agg_pop


    def agg_IVS_por_cluster(self):
        """
        IVS vai ser a média de cada um dos setores normalizados (proporcao da pop)
        Verificar se sao a mesma coisa (Dados do Drive e dados dos cluster)
        """
        df_agg_IVS = self.df_setor_censitario.groupby(by="cluster").agg({'Índice': "mean"}).reset_index()
        return df_agg_IVS


    def calcula_centro_cluster(self):
        """
        usei o método da média simples porque depois de uma pesquisa vi que esse é o mais comum e mais eficiente para nossa 
        aplicacao. Contudo, verificar explicabilidade do método
        """
        lat_final = list()
        long_final = list()
        cluster_final = list()
        for cl in self.df_setor_censitario.cluster.unique():
            df_aux = self.df_setor_censitario[self.df_setor_censitario.cluster == cl]
            lista_lats = df_aux.LAT.to_list()
            lista_long = df_aux.LONG.to_list()
            lat_central = sum(lista_lats) / len(lista_lats)
            lon_central = sum(lista_long) / len(lista_long)
            lat_final.append(lat_central)
            long_final.append(lon_central)
            cluster_final.append(cl)

        df_agg_coords = pd.DataFrame({"cluster": cluster_final, "LAT":lat_final, "LONG": long_final})
        return df_agg_coords


    def allocate_exists_PHC_in_cluster_and_define_geo_coords(self, df_agg_coords):
        """
        DÚVIDA:
        O modelo de dados hoje considera que as equipes estao em setores censitarios, e nao nas coordenadas das UBS em si.
        Vou manter assim e agrupar por cluster, mas validar se é possivel considerar as UBS sem estar dentro dos setores.
        Outro ponto é que podemos ter imprecisao para saber de onde enviar ou colocar recursos.

        """
        cols_PHC = ['CO_UNIDADE', "cluster"] + [i for i in self.df_setor_censitario.columns if isinstance(i, float)]
        df_PHC = self.df_setor_censitario[self.df_setor_censitario["CO_UNIDADE_UBS"] != 0][cols_PHC].reset_index()
        df_PHC = df_PHC.merge(df_agg_coords, on="cluster", how="inner")

        
        return df_PHC

    def convert_setor_censitario_em_cluster(self):
        self.read_and_format_SC_to_cluster_data()
        self.merge_cluster_in_SC_data()
        df_agg_pop = self.agg_populacao_por_cluster()
        df_agg_IVS = self.agg_IVS_por_cluster()
        df_agg_coords = self.calcula_centro_cluster()

        self.df_agg_cluster = (
            df_agg_pop
            .merge(df_agg_IVS, on="cluster", how="inner")
            .merge(df_agg_coords, on="cluster", how="inner")
        )

        self.df_PHC_by_cluster = self.allocate_exists_PHC_in_cluster_and_define_geo_coords(df_agg_coords)


    def build(self):
        self.read_and_format_path_arquivo_setores_censitarios()
        self.read_and_format_path_setores_com_UBS()
        self.read_and_format_dados_IVS()
        self.read_and_format_path_equipes_PHC()
        if self.path_arquivos_data.path_cluster_CSV:
            self.convert_setor_censitario_em_cluster()

        # path_d = f"dados_{self.configuration_data.municipio}.xlsx"
        # self.df_setor_censitario.to_excel(path_d)
        b=0
        dist_PHC_SC = None
        dist_SC_SC = None
        if self.create_distance_data:
            instance_data_creator = DistanceAPICalculator(
                                                        self.path_arquivos_data.path_json_distances,
                                                        self.df_setor_censitario,  )
            dist_PHC_SC, dist_SC_SC =  instance_data_creator.build()                                       
        return {"dfs": self.df_setor_censitario, "configurations": self.configuration_data, "create_distance_data": self.create_distance_data,
                "dist_PHC_SC": dist_PHC_SC, "dist_SC_SC": dist_SC_SC}
