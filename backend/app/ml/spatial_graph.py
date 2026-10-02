"""
ZYNORA-ML — Spatial Topological Graph Engine
Converts room programs and physical boundary constraints into attributed spatial adjacency graphs.
"""
import networkx as nx
from typing import Dict, Any, List

class SpatialGraphBuilder:
    def __init__(self):
        self.public_zones = ["living", "dining", "kitchen", "porch", "veranda"]
        self.private_zones = ["bedroom", "bathroom", "study"]
        self.service_zones = ["utility", "parking", "pantry"]

    def build_program_graph(self, family_data: Dict[str, Any], property_data: Dict[str, Any]) -> nx.Graph:
        """
        Constructs an attributed Graph G = (V, E)
        Nodes = Habitable spaces with target areas & constraints
        Edges = Spatial circulation & acoustic adjacency constraints
        """
        G = nx.Graph()
        rooms = family_data.get("rooms", {})
        reqs = family_data.get("requirements", [])
        total_builtup = property_data.get("builtUpArea", 3800)

        # 1. Add Entry / Arrival Node
        G.add_node("Entry_Foyer", type="circulation", area=120, daylight_priority="medium", zone="public")

        # 2. Add Living Pavilion
        living_count = rooms.get("livingRoom", 1)
        for i in range(living_count):
            node_id = f"Living_Room_{i+1}" if living_count > 1 else "Living_Room"
            G.add_node(node_id, type="living", area=540, daylight_priority="high", zone="public")
            G.add_edge("Entry_Foyer", node_id, weight=1.0, relation="direct_access")

        # 3. Add Kitchen & Dining
        dining_count = rooms.get("dining", 1)
        for i in range(dining_count):
            node_id = f"Dining_Room_{i+1}" if dining_count > 1 else "Dining_Room"
            G.add_node(node_id, type="dining", area=240, daylight_priority="high", zone="public")
            G.add_edge("Living_Room", node_id, weight=1.0, relation="open_adj")

        kitchen_count = rooms.get("kitchen", 1)
        for i in range(kitchen_count):
            node_id = f"Chef_Kitchen_{i+1}" if kitchen_count > 1 else "Chef_Kitchen"
            G.add_node(node_id, type="kitchen", area=280, daylight_priority="medium", zone="service")
            G.add_edge("Dining_Room", node_id, weight=1.0, relation="direct_access")

        # 4. Add Bedrooms & En Suites
        bed_count = rooms.get("bedrooms", 4)
        for i in range(bed_count):
            is_master = (i == 0)
            node_id = "Master_Suite" if is_master else f"Bedroom_{i+1}"
            area = 420 if is_master else 220
            G.add_node(node_id, type="bedroom", area=area, daylight_priority="high", zone="private", is_master=is_master)
            
            # Master connects via corridor
            G.add_edge("Entry_Foyer", node_id, weight=2.0, relation="private_corridor")

            # Dedicated Bath
            bath_id = f"Bath_Master" if is_master else f"Bath_{i+1}"
            G.add_node(bath_id, type="bathroom", area=90, daylight_priority="low", zone="private")
            G.add_edge(node_id, bath_id, weight=0.5, relation="en_suite")

        # 5. Study / Work Studio
        study_count = rooms.get("study", 1)
        for i in range(study_count):
            node_id = f"Executive_Study_{i+1}" if study_count > 1 else "Executive_Study"
            G.add_node(node_id, type="study", area=190, daylight_priority="high", zone="private")
            G.add_edge("Entry_Foyer", node_id, weight=1.5, relation="semi_private")

        # 6. Service / Utility
        utility_count = rooms.get("utility", 1)
        for i in range(utility_count):
            node_id = f"Utility_{i+1}" if utility_count > 1 else "Utility_Laundry"
            G.add_node(node_id, type="utility", area=160, daylight_priority="low", zone="service")
            G.add_edge("Chef_Kitchen", node_id, weight=0.8, relation="service_access")

        # Compute graph metrics
        for n in G.nodes():
            G.nodes[n]["degree"] = G.degree(n)
            G.nodes[n]["closeness"] = nx.closeness_centrality(G, n)

        return G

    def extract_circulation_tree(self, G: nx.Graph, root: str = "Entry_Foyer") -> List[Dict[str, Any]]:
        """Computes breadth-first traversal paths from main entry"""
        paths = []
        for target in G.nodes():
            if target != root:
                try:
                    sp = nx.shortest_path(G, source=root, target=target)
                    paths.append({
                        "destination": target,
                        "hops": len(sp) - 1,
                        "path": sp,
                        "zone": G.nodes[target].get("zone", "public")
                    })
                except nx.NetworkXNoPath:
                    pass
        return paths
