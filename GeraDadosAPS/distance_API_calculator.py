import pandas as pd
import json
import time
from openrouteservice_internal import ORSMatrixClient
import openrouteservice

API_KEY = "5b3ce3597851110001cf62487cf120e8b42a44379bf9e0833928b80c"

class DistanceAPICalculator:
    def __init__(self, path_jsons_instances, df_setor_censitario):
        self.path_jsons_instances = path_jsons_instances
        self.df_setor_censitario = df_setor_censitario
        self.json_dist_format = dict()
        self.client = ORSMatrixClient(api_key=API_KEY, profile='driving-car')
    
    def build(self):
        self.create_origin_dest_PHC_SC()
        self.create_origin_dest_SC_to_SC()
        self.read_and_format_json()
        dist_PHC_SC = self.get_distances(self.origin_dest_PHC_SC)
        dist_SC_SC = self.get_distances(self.origin_dest_SC_to_SC)
        
        return dist_PHC_SC, dist_SC_SC

    def create_base_json_to_get_full_matrix(self):
        SC_id = self.df_setor_censitario.SETOR.to_list()
        SC_lat = self.df_setor_censitario.LAT.to_list()
        SC_long = self.df_setor_censitario.LONG.to_list()
        self.data_dist = {"sectors": []}
        for o_id, o_lat, o_long in zip(SC_id, SC_lat, SC_long):
            self.data_dist["sectors"].append({"setor": o_id, "latitude": o_lat, "longitude": o_long})

        self.name_instance_data_matriz = "lagoa_santa_teste.json" #TODO: Parametrizar isso!
        with open("lagoa_santa_teste.json", "w", encoding="utf-8") as f:
            json.dump(self.data_dist, f)

    def get_full_dist_matriz_from_API(self):
       
        output_file_distance = "lagoa_santa_distance_test.json"
        try:
            # Choose your batching strategy:
            
            # Full cross-batch matrix (ALL possible pairs)
            # Good for: When you need distances between ALL locations
            # Warning: This makes many more API calls!
                    
            # Uncomment the following lines if you want the full matrix:
            results = self.client.process_cross_batch_matrix(
                # input_file="LagoaSanta.json",
                # output_file="LagoaSanta_matrix_results_full_matrix.json",
                # input_file="Divinopolis.json",
                # output_file="Divinopolis_matrix_results_full_matrix.json",
                # input_file="MontesClaros.json",
                # output_file="MontesClaros_matrix_results_full_matrix.json",
                # input_file="Contagem.json",
                # output_file="Contagem_matrix_results_full_matrix.json",
                input_file=self.name_instance_data_matriz,
                output_file=output_file_distance,
                batch_size=10,
                delay_between_batches=2.0  # Longer delay for rate limiting
            )
    
            print(f"\nSimple batching generated {len(results)} origin-destination pairs")
            self.path_jsons_instances = output_file_distance
        # Display first few results
            print("\nSample results:")
            for i, result in enumerate(results[:3]):
                print(f"\nResult {i+1}:")
                print(f"Origin: {result['origin']['setor']}")
                print(f"Destination: {result['destination']['setor']}")
                print(f"Distance: {result.get('distance_km', 'N/A')} km")
                print(f"Duration: {result.get('duration_minutes', 'N/A')} minutes")
                
        except Exception as e:
                print(f"Error: {e}")
                print("\nCommon causes of 400 Bad Request:")
                print("1. Invalid API key")
                print("2. Too many locations per batch")
                print("3. Invalid coordinate format")
                print("4. Coordinates outside service area")
                print("5. Rate limit exceeded")
                print("\nTips for batching:")
                print("- Use batch_size=25 for free tier")
                print("- Use batch_size=50 for paid plans")
                print("- Increase delay_between_batches if you hit rate limits")
                        
    def read_and_format_json(self):
        if not self.path_jsons_instances:
            self.create_base_json_to_get_full_matrix()
            self.get_full_dist_matriz_from_API()

        with open(self.path_jsons_instances, encoding="utf-8") as f:
            json_dist = (json.load(f))


        for item in json_dist:
            o = item["origin"]["setor"]
            d = item["destination"]["setor"]
            self.json_dist_format[(o, d)] = item['distance_meters'] #TODO: Flag nas configuracoes para saber o que usar de distancia!

    def create_origin_dest_PHC_SC(self):
        SC_id = self.df_setor_censitario.SETOR.to_list()
        SC_lat = self.df_setor_censitario.LAT.to_list()
        SC_long = self.df_setor_censitario.LONG.to_list()
        df_UBS = self.df_setor_censitario[self.df_setor_censitario.CO_UNIDADE_UBS > 0 ]
        PHC_id = df_UBS.SETOR.to_list()
        PHC_lat = df_UBS.LAT.to_list()
        PHC_long = df_UBS.LONG.to_list()
        origin_dest_pairs = {}

        for o_id, o_lat, o_long in zip(PHC_id, PHC_lat, PHC_long):
            for d_id, d_lat, d_long in zip(SC_id, SC_lat, SC_long):
                origin_dest_pairs[(o_id, d_id)] = {
                    "origin": {
                        "id": o_id,
                        "lat": o_lat,
                        "long": o_long,
                    },
                    "destination": {
                        "id": d_id,
                        "lat": d_lat,
                        "long": d_long,
                    },
                }

        # guarda no objeto para uso posterior
        self.origin_dest_PHC_SC = origin_dest_pairs

    def create_origin_dest_SC_to_SC(self):
        SC_id = self.df_setor_censitario.SETOR.to_list()
        SC_lat = self.df_setor_censitario.LAT.to_list()
        SC_long = self.df_setor_censitario.LONG.to_list()
        origin_dest_pairs = {}

        for o_id, o_lat, o_long in zip(SC_id, SC_lat, SC_long):
            for d_id, d_lat, d_long in zip(SC_id, SC_lat, SC_long):
                origin_dest_pairs[(o_id, d_id)] = {
                    "origin": {
                        "id": o_id,
                        "lat": o_lat,
                        "long": o_long,
                    },
                    "destination": {
                        "id": d_id,
                        "lat": d_lat,
                        "long": d_long,
                    },
                }

        # guarda no objeto para uso posterior
        self.origin_dest_SC_to_SC = origin_dest_pairs

    def _get_cached_distance(self, origem, destino):
        key1 = (origem, destino)
        key2 = (destino, origem)

        return (
            self.json_dist_format.get(key1)
            or self.json_dist_format.get(key2)
            )

    def _fetch_distance_with_fallback(self, dt):
        time.sleep(0.1)  # rate limit

        try:
            return self.get_distance_in_API(dt)
        except Exception:
            return self.get_calculate_aproximated_distance(dt)

    def get_distances(self, origin_dest_PHC_SC):
        dict_dist_final = list()
        for (sc_origem, sc_destino), dt in origin_dest_PHC_SC.items():
            if sc_origem == sc_destino:
                dist = 0
            else:
                dist = self._get_cached_distance(sc_origem, sc_destino)

                if dist is None:
                    print(f"fallback_{sc_origem}_{sc_destino}")
                    dist = self._fetch_distance_with_fallback(dt)

                dict_dist_final.append({
                    "origem": sc_origem,
                    "destino": sc_destino,
                    "distancia": dist
                })

        return dict_dist_final

    def get_calculate_aproximated_distance(self, dt):
        pass
    

    def get_distance_in_API(self, dados_og):
        # Origem e destino (lon, lat)
        origem = (dados_og["origin"]["long"], dados_og["origin"]["lat"])
        destino = (dados_og["destination"]["long"], dados_og["origin"]["lat"])
        client = openrouteservice.Client(key=API_KEY)
        rota = client.directions(
            coordinates=[origem, destino],
            profile='driving-car',
            format='json'
        )

        #dist_m = rota['routes'][0]['summary']['distance']
        dist_m = rota['routes'][0]['segments'][0]['distance']
        return dist_m



    # def read_distances_from_json(self):
    #     self.df_json_distances = pd.read_json(self.path_jsons_instances)
    #     self.read_distances_PHC_SC()
    #     self.read_distances_SC_to_all_SC()

