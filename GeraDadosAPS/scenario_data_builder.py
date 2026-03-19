import pandas as pd


from Configuration_data import ConfigurationDataScenario, PathArquivoDados, ExecutionDataType
from distance_API_calculator import DistanceAPICalculatorBySC, DistanceAPICalculatorByCluster


class ScenarioDataBuilder():
    def __init__(self, 
                configuration_data:ConfigurationDataScenario,
                path_arquivos_data: PathArquivoDados,
                create_distance_data:bool
                ) -> None:

        self.configuration_data = configuration_data
        self.path_arquivos_data = path_arquivos_data
        self.create_distance_data = create_distance_data
        #Será que vale separar em 3 classes ?



    def read_and_format_path_arquivo_setores_censitarios(self):
        #df = pd.read_excel(self.path_arquivos_data.path_arquivo_setores_censitarios)
        #df = pd.read_excel(r"C:\aps\GeraDadosAPS\Dados\Lagoa Santa\dados_brutos\dados_setor_censitario_LAGOA_SANTA.xlsx")
        df = pd.read_excel(r"C:\aps\GeraDadosAPS\Dados\Contagem\dados_brutos\dados_setor_censitario_CONTAGEM.xlsx")
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
        #self.df_setor_censitario["cluster"] = self.df_setor_censitario["cluster"].astype(int)
        self.df_setor_censitario["cluster"] = self.df_setor_censitario["cluster"].apply(lambda x: f"CLU_{int(x)}")

    def agg_populacao_por_cluster(self):
        """
        Premissa de agregacao da populacao:
        Somar a populacao de todos os setores do cluster
        """
        df_agg_pop = self.df_setor_censitario.groupby(by="cluster").agg({"V01006": "sum"}).reset_index()
        df_agg_pop["V01006"] = round(df_agg_pop["V01006"], 3)
        return df_agg_pop


    def agg_IVS_por_cluster(self):
        """
        IVS vai ser a média de cada um dos setores normalizados (proporcao da pop)
        Verificar se sao a mesma coisa (Dados do Drive e dados dos cluster)
        """
        df_agg_IVS = self.df_setor_censitario.groupby(by="cluster").agg({'Índice': "mean"}).reset_index()
        df_agg_IVS['Índice'] = round(df_agg_IVS['Índice'], 3)
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
        cols_PHC = ['CO_UNIDADE', "cluster", "PORTE_UBS"] + [i for i in self.df_setor_censitario.columns if isinstance(i, float)]
        df_PHC = self.df_setor_censitario[self.df_setor_censitario["CO_UNIDADE_UBS"] != 0][cols_PHC].reset_index()
        self.df_PHC_by_cluster = df_PHC.merge(df_agg_coords, on="cluster", how="inner")

    
    def  set_cluster_to_be_candidate_locations(self):
        """
        Método que vai definir quais sao os cluster que vao ser locais candidatos 
        Aqui deve ser incluído o script ou os dados gerados pelo bruno e claudinele. 
        Inicialmente vou considerar todos os cluster como locais candidatos
    
        """
        self.df_clusters_candidates_PHC_locations = self.df_agg_cluster[["cluster", "LAT", "LONG"]].copy()
        #self.df_clusters_candidates_PHC_locations["CO_UNIDADE"] = self.df_clusters_candidates_PHC_locations.cluster.apply(lambda x: f"CL_cluster_{int(x)}")
        self.df_clusters_candidates_PHC_locations["CO_UNIDADE"] = self.df_clusters_candidates_PHC_locations.cluster

    def set_full_PHC_locations(self):
        """
        Método que vai gerar o dataframe final com a juncao das PHC existentes com os cluster candidatos.
        Importante lembrar que esse conjunto NAO irá para os .dat porque será concatenado no .mod para ter
        mais um mecanismo de validacao dos dados. 
        Porém, para o calculo das distancias, ele será util.        
        """
        # PHC existentes: mantemos CO_UNIDADE numérico
        self.df_PHC_by_cluster["CO_UNIDADE"] = self.df_PHC_by_cluster["CO_UNIDADE"].astype(int)
        self.df_PHC_by_cluster["CO_UNIDADE"] = self.df_PHC_by_cluster["CO_UNIDADE"].astype(int)
        # Locais candidatos (clusters) já têm CO_UNIDADE como string (ex.: "CL_cluster_X"),
        # então não convertimos para int para preservar a distinção entre eles.
        self.df_full_PHC_locations =  pd.concat([self.df_PHC_by_cluster, self.df_clusters_candidates_PHC_locations], ignore_index = True)
        self.df_full_PHC_locations = self.df_full_PHC_locations.fillna(0)


    def convert_setor_censitario_em_cluster(self):
        #TODO: Isso deveria ser uma classe separada ?
        self.read_and_format_SC_to_cluster_data()
        self.merge_cluster_in_SC_data()
        df_agg_pop = self.agg_populacao_por_cluster()
        df_agg_IVS = self.agg_IVS_por_cluster()
        df_agg_coords = self.calcula_centro_cluster()

        #TODO: set this in a method!
        self.df_agg_cluster = (
            df_agg_pop
            .merge(df_agg_IVS, on="cluster", how="inner")
            .merge(df_agg_coords, on="cluster", how="inner")
        )

        self.allocate_exists_PHC_in_cluster_and_define_geo_coords(df_agg_coords)
        self.set_cluster_to_be_candidate_locations()
        self.set_full_PHC_locations()


    def read_and_format_SIZE_PHC(self):
        df_porte_ubs = pd.read_excel(self.path_arquivos_data.path_porte_UBS)
        df_porte_ubs.rename(columns={"UBS.PORTE": "PORTE_UBS"}, inplace=True)
        df_porte_ubs["PORTE_UBS"] = df_porte_ubs["PORTE_UBS"].astype(int)
        self.df_setor_censitario = self.df_setor_censitario.merge(df_porte_ubs[["CO_UNIDADE", "PORTE_UBS"]], on="CO_UNIDADE",  how="left")
    
    def build(self):
        self.read_and_format_path_arquivo_setores_censitarios()
        self.read_and_format_path_setores_com_UBS()
        self.read_and_format_dados_IVS()
        self.read_and_format_path_equipes_PHC()
        self.read_and_format_SIZE_PHC()
        if self.configuration_data.tipo_rodada == ExecutionDataType.BY_CLUSTER:
            self.convert_setor_censitario_em_cluster()
            distance_data_creator = DistanceAPICalculatorByCluster(self.df_agg_cluster, 
                                                                  self.df_full_PHC_locations,
                                                                  "lalala")
            dist_SC_PHC, dist_PHC_PHC =  distance_data_creator.build()  
            return {"df_demanda": self.df_agg_cluster, 
                    "df_PHC_exists_and_candidadtes":self.df_full_PHC_locations, 
                    "configurations": self.configuration_data, 
                    "create_distance_data": self.create_distance_data,
                    "dist_SC_PHC": dist_SC_PHC, "dist_PHC_PHC": dist_PHC_PHC}

        else:
            dist_PHC_SC = None
            dist_SC_SC = None
            if self.create_distance_data:
                distance_data_creator = DistanceAPICalculatorBySC(
                                                            self.path_arquivos_data.path_json_distances,
                                                            self.df_setor_censitario,
                                                            "lala"  )
                                                            
                #TODO MASTER: LEMBRAR QUE AS DISTANCIAS PRECISAM SER DO SETOR CENSITARIO PARA TODOS OS PHCS E PHCS E PHCS
                dist_PHC_SC, dist_SC_SC =  distance_data_creator.build() 

            return {"dfs": self.df_setor_censitario, "configurations": self.configuration_data, "create_distance_data": self.create_distance_data,
                        "dist_PHC_SC": dist_PHC_SC, "dist_SC_SC": dist_SC_SC}
