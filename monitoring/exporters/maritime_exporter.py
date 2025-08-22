#!/usr/bin/env python3
"""
Maritime Intelligence Prometheus Exporter

This exporter generates realistic maritime metrics for demonstration purposes.
In a production environment, this would connect to real AIS data feeds,
port management systems, and other maritime data sources.
"""

import time
import random
import math
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaritimeExporter:
    def __init__(self):
        # Vessel position and movement metrics
        self.vessel_latitude = Gauge('vessel_latitude', 'Vessel latitude position', 
                                   ['vessel_id', 'vessel_name', 'vessel_type', 'flag'])
        self.vessel_longitude = Gauge('vessel_longitude', 'Vessel longitude position', 
                                    ['vessel_id', 'vessel_name', 'vessel_type', 'flag'])
        self.vessel_speed = Gauge('vessel_speed_knots', 'Vessel speed in knots', 
                                ['vessel_id', 'vessel_name', 'vessel_type', 'flag'])
        self.vessel_heading = Gauge('vessel_heading_degrees', 'Vessel heading in degrees', 
                                  ['vessel_id', 'vessel_name', 'vessel_type', 'flag'])
        
        # Vessel operational metrics
        self.vessel_cargo_capacity = Gauge('vessel_cargo_capacity_teu', 'Vessel cargo capacity in TEU', 
                                         ['vessel_id', 'vessel_name', 'vessel_type'])
        self.vessel_cargo_current = Gauge('vessel_cargo_current_teu', 'Current cargo load in TEU', 
                                        ['vessel_id', 'vessel_name', 'vessel_type'])
        self.vessel_fuel_level = Gauge('vessel_fuel_level_percent', 'Fuel level percentage', 
                                     ['vessel_id', 'vessel_name', 'vessel_type'])
        self.vessel_engine_rpm = Gauge('vessel_engine_rpm', 'Engine RPM', 
                                     ['vessel_id', 'vessel_name', 'vessel_type'])
        
        # Port metrics
        self.port_vessel_count = Gauge('port_vessel_count', 'Number of vessels at port', 
                                     ['port_code', 'port_name', 'country'])
        self.port_berth_occupancy = Gauge('port_berth_occupancy_percent', 'Port berth occupancy percentage', 
                                        ['port_code', 'port_name', 'country'])
        self.port_queue_length = Gauge('port_queue_length', 'Number of vessels waiting', 
                                     ['port_code', 'port_name', 'country'])
        self.port_avg_turnaround = Gauge('port_avg_turnaround_hours', 'Average turnaround time in hours', 
                                       ['port_code', 'port_name', 'country'])
        
        # Route and traffic metrics
        self.shipping_lane_traffic = Gauge('shipping_lane_traffic_count', 'Number of vessels in shipping lane', 
                                         ['lane_id', 'lane_name', 'direction'])
        self.route_efficiency = Gauge('route_efficiency_percent', 'Route efficiency percentage', 
                                    ['route_id', 'origin_port', 'destination_port'])
        
        # Business intelligence metrics
        self.fleet_utilization = Gauge('fleet_utilization_percent', 'Fleet utilization percentage', 
                                     ['operator', 'vessel_type'])
        self.cargo_throughput = Counter('cargo_throughput_teu_total', 'Total cargo throughput in TEU', 
                                      ['port_code', 'cargo_type'])
        self.voyage_duration = Histogram('voyage_duration_hours', 'Voyage duration in hours', 
                                       ['origin_port', 'destination_port', 'vessel_type'])
        
        # Risk and compliance metrics
        self.vessel_risk_score = Gauge('vessel_risk_score', 'Vessel risk score (0-100)', 
                                     ['vessel_id', 'risk_category'])
        self.compliance_status = Gauge('compliance_status', 'Compliance status (1=compliant, 0=non-compliant)', 
                                     ['vessel_id', 'regulation_type'])
        
        # Initialize simulation data
        self.vessels = self._initialize_vessels()
        self.ports = self._initialize_ports()
        self.shipping_lanes = self._initialize_shipping_lanes()
        
        logger.info(f"Initialized maritime exporter with {len(self.vessels)} vessels and {len(self.ports)} ports")

    def _initialize_vessels(self) -> List[Dict]:
        """Initialize a fleet of vessels with realistic data"""
        vessel_types = [
            ('Container Ship', 'CONTAINER', 2000, 8000),
            ('Bulk Carrier', 'BULK', 1500, 6000),
            ('Tanker', 'TANKER', 1000, 4000),
            ('General Cargo', 'GENERAL', 500, 2000),
            ('RoRo', 'RORO', 800, 3000)
        ]
        
        flags = ['MH', 'LR', 'PA', 'SG', 'MT', 'CY', 'GB', 'NO', 'DK', 'NL']
        operators = ['Maersk', 'MSC', 'COSCO', 'CMA CGM', 'Hapag-Lloyd', 'ONE', 'Yang Ming']
        
        vessels = []
        for i in range(50):  # 50 vessels for demonstration
            vessel_type_data = random.choice(vessel_types)
            vessel = {
                'id': f'V{i+1:04d}',
                'name': f'{random.choice(["Star", "Ocean", "Global", "Pacific", "Atlantic"])} {random.choice(["Trader", "Pioneer", "Voyager", "Navigator", "Explorer"])}',
                'type': vessel_type_data[1],
                'type_name': vessel_type_data[0],
                'flag': random.choice(flags),
                'operator': random.choice(operators),
                'capacity': random.randint(vessel_type_data[2], vessel_type_data[3]),
                'current_cargo': 0,
                'fuel_level': random.uniform(30, 95),
                # Start with random positions in major shipping areas
                'latitude': random.uniform(-60, 70),
                'longitude': random.uniform(-180, 180),
                'speed': random.uniform(0, 25),
                'heading': random.uniform(0, 360),
                'status': random.choice(['underway', 'at_anchor', 'in_port', 'moored']),
                'last_port': None,
                'next_port': None,
                'voyage_start': datetime.now() - timedelta(hours=random.randint(1, 168))
            }
            vessels.append(vessel)
        
        return vessels

    def _initialize_ports(self) -> List[Dict]:
        """Initialize major global ports"""
        ports_data = [
            ('SGSIN', 'Singapore', 'Singapore', 1.290, 103.851, 150),
            ('CNSHA', 'Shanghai', 'China', 31.230, 121.474, 200),
            ('NLRTM', 'Rotterdam', 'Netherlands', 51.924, 4.477, 120),
            ('CNNGB', 'Ningbo', 'China', 29.868, 121.544, 100),
            ('CNSZX', 'Shenzhen', 'China', 22.543, 114.057, 90),
            ('KRPUS', 'Busan', 'South Korea', 35.104, 129.042, 80),
            ('HKHKG', 'Hong Kong', 'Hong Kong', 22.302, 114.177, 85),
            ('DEHAM', 'Hamburg', 'Germany', 53.551, 9.994, 70),
            ('USNYC', 'New York', 'United States', 40.693, -74.044, 110),
            ('USLAX', 'Los Angeles', 'United States', 33.742, -118.266, 130),
            ('AEDXB', 'Dubai', 'UAE', 25.276, 55.296, 95),
            ('LKCMB', 'Colombo', 'Sri Lanka', 6.932, 79.857, 60),
            ('MYPKG', 'Port Klang', 'Malaysia', 3.006, 101.399, 75),
            ('VNVUT', 'Vung Tau', 'Vietnam', 10.346, 107.084, 45),
            ('THBKK', 'Laem Chabang', 'Thailand', 13.086, 100.883, 55)
        ]
        
        ports = []
        for port_data in ports_data:
            port = {
                'code': port_data[0],
                'name': port_data[1],
                'country': port_data[2],
                'latitude': port_data[3],
                'longitude': port_data[4],
                'berth_capacity': port_data[5],
                'current_occupancy': random.randint(30, 95),
                'queue_length': random.randint(0, 15),
                'avg_turnaround': random.uniform(8, 72)
            }
            ports.append(port)
        
        return ports

    def _initialize_shipping_lanes(self) -> List[Dict]:
        """Initialize major shipping lanes"""
        return [
            {'id': 'TSS001', 'name': 'Singapore Strait', 'direction': 'eastbound'},
            {'id': 'TSS001', 'name': 'Singapore Strait', 'direction': 'westbound'},
            {'id': 'TSS002', 'name': 'Dover Strait', 'direction': 'northbound'},
            {'id': 'TSS002', 'name': 'Dover Strait', 'direction': 'southbound'},
            {'id': 'TSS003', 'name': 'Suez Canal', 'direction': 'northbound'},
            {'id': 'TSS003', 'name': 'Suez Canal', 'direction': 'southbound'},
            {'id': 'TSS004', 'name': 'Panama Canal', 'direction': 'eastbound'},
            {'id': 'TSS004', 'name': 'Panama Canal', 'direction': 'westbound'},
            {'id': 'LANE001', 'name': 'Trans-Pacific', 'direction': 'eastbound'},
            {'id': 'LANE001', 'name': 'Trans-Pacific', 'direction': 'westbound'},
            {'id': 'LANE002', 'name': 'Trans-Atlantic', 'direction': 'eastbound'},
            {'id': 'LANE002', 'name': 'Trans-Atlantic', 'direction': 'westbound'}
        ]

    def _simulate_vessel_movement(self, vessel: Dict) -> None:
        """Simulate realistic vessel movement"""
        # Simple movement simulation - in reality this would be much more complex
        if vessel['status'] == 'underway':
            # Move vessel based on speed and heading
            speed_ms = vessel['speed'] * 0.514444  # Convert knots to m/s
            distance_deg = (speed_ms * 300) / 111000  # Rough conversion to degrees (5-minute update cycle)
            
            # Update position
            lat_change = distance_deg * math.cos(math.radians(vessel['heading']))
            lon_change = distance_deg * math.sin(math.radians(vessel['heading']))
            
            vessel['latitude'] += lat_change
            vessel['longitude'] += lon_change
            
            # Ensure coordinates stay within valid ranges
            vessel['latitude'] = max(-90, min(90, vessel['latitude']))
            vessel['longitude'] = max(-180, min(180, vessel['longitude']))
            
            # Occasionally change course slightly
            if random.random() < 0.1:
                vessel['heading'] += random.uniform(-10, 10)
                vessel['heading'] = vessel['heading'] % 360
                
            # Occasionally change speed
            if random.random() < 0.05:
                vessel['speed'] += random.uniform(-2, 2)
                vessel['speed'] = max(0, min(25, vessel['speed']))
            
            # Consume fuel
            vessel['fuel_level'] -= random.uniform(0.01, 0.05)
            vessel['fuel_level'] = max(0, vessel['fuel_level'])
            
        elif vessel['status'] == 'in_port':
            # Vessel is stationary, might be loading/unloading
            if random.random() < 0.02:  # 2% chance to change cargo
                if vessel['current_cargo'] < vessel['capacity'] * 0.8:
                    vessel['current_cargo'] += random.randint(50, 200)
                vessel['current_cargo'] = min(vessel['capacity'], vessel['current_cargo'])

    def update_metrics(self):
        """Update all maritime metrics"""
        
        # Update vessel positions and operational data
        for vessel in self.vessels:
            self._simulate_vessel_movement(vessel)
            
            # Update vessel position metrics
            labels = [vessel['id'], vessel['name'], vessel['type'], vessel['flag']]
            self.vessel_latitude.labels(*labels).set(vessel['latitude'])
            self.vessel_longitude.labels(*labels).set(vessel['longitude'])
            self.vessel_speed.labels(*labels).set(vessel['speed'])
            self.vessel_heading.labels(*labels).set(vessel['heading'])
            
            # Update operational metrics
            op_labels = [vessel['id'], vessel['name'], vessel['type']]
            self.vessel_cargo_capacity.labels(*op_labels).set(vessel['capacity'])
            self.vessel_cargo_current.labels(*op_labels).set(vessel['current_cargo'])
            self.vessel_fuel_level.labels(*op_labels).set(vessel['fuel_level'])
            self.vessel_engine_rpm.labels(*op_labels).set(random.uniform(800, 2000))
            
            # Risk and compliance metrics
            risk_score = random.uniform(0, 100)
            self.vessel_risk_score.labels(vessel['id'], 'operational').set(risk_score)
            self.compliance_status.labels(vessel['id'], 'emissions').set(1 if risk_score < 70 else 0)
        
        # Update port metrics
        for port in self.ports:
            # Simulate some variation in port metrics
            port['current_occupancy'] += random.uniform(-2, 2)
            port['current_occupancy'] = max(20, min(100, port['current_occupancy']))
            
            port['queue_length'] += random.randint(-1, 2)
            port['queue_length'] = max(0, port['queue_length'])
            
            port_labels = [port['code'], port['name'], port['country']]
            vessels_at_port = len([v for v in self.vessels if v['status'] == 'in_port'])
            
            self.port_vessel_count.labels(*port_labels).set(vessels_at_port)
            self.port_berth_occupancy.labels(*port_labels).set(port['current_occupancy'])
            self.port_queue_length.labels(*port_labels).set(port['queue_length'])
            self.port_avg_turnaround.labels(*port_labels).set(port['avg_turnaround'])
        
        # Update shipping lane traffic
        for lane in self.shipping_lanes:
            traffic_count = random.randint(5, 50)
            self.shipping_lane_traffic.labels(lane['id'], lane['name'], lane['direction']).set(traffic_count)
        
        # Update business intelligence metrics
        for operator in set(v['operator'] for v in self.vessels):
            for vessel_type in set(v['type'] for v in self.vessels):
                utilization = random.uniform(60, 95)
                self.fleet_utilization.labels(operator, vessel_type).set(utilization)
        
        # Simulate some cargo throughput
        if random.random() < 0.1:  # 10% chance per update cycle
            port = random.choice(self.ports)
            cargo_types = ['containers', 'bulk', 'liquid', 'general']
            self.cargo_throughput.labels(port['code'], random.choice(cargo_types)).inc(random.randint(10, 100))

def main():
    """Main function to run the maritime exporter"""
    exporter = MaritimeExporter()
    
    # Start the HTTP server
    start_http_server(8000)
    logger.info("Maritime exporter started on port 8000")
    
    # Update metrics every 5 minutes (300 seconds)
    while True:
        try:
            exporter.update_metrics()
            logger.info("Updated maritime metrics")
            time.sleep(300)  # Update every 5 minutes
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == '__main__':
    main()