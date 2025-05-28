# DataCoolSim
DataCoolSim is a PyQT desktop app that makes data centers' transition to a sustainable future more seamless. DataCoolSim models a data center's performance with an immersion cooling system to provide owners with the dimensions and rationale for their data center's upgrade.
Immersion cooling works by submerging the individual servers in a dielectric fluid (a fluid incapable of conducting electricity) to transfer heat away from the server in a more renewable fashion. Our implementation of immersion cooling works by submerging the entire server, not just components, in the fluid. We use a single-phase immersion cooling system, where the dielectric fluid is used by itself, rather than a double-phase, where the liquid is converted into a gas. This eliminates potential points of failures as well as simplifying the system, making it easier for data center owners to make the switch to the future.

Users input information about their data center racks, and are given insights about their energy usage and thermal efficiency with a traditional air-cooled system vs. a liquid-cooled system. DataCoolSim's model takes into account a myriad of features relevant to the model's calculations, which are listed below:
- Ambient Air Temperature (Celsius) of the environment
- Number of Servers
- Heat load per Server (watts)
- Fan Airflow (meters cubed/second)
- Fan Efficiency (Percent represented as a decimal 0-1)
- Dust Accumulation Factor (Percent represented as a decimal of how much interference the dust may have on cooling)
- Heatsink Efficiency (Percent represented as a decimal 0-1)
- Heatsink Surface Area (meters cubed)
- Air Duct length (meters)
- Air Duct Diameter (meters)
- Temperature of Coolant upon Input (Celsius)
- Surface Area per Server (meters squared)
- Server Age in Runtime Hours (represented as tau)
- Distance from Heat Exchanger
- Insulation Type
- Dielectric Fluid Type
- Volumetric Flow Rate (meters cubed/second)
- Flow Area (meters squared)
- Characteristic (Reference) Length (meters)
- Rack ID in Column
- Pipe Length (meters)
- Pipe Roughness (meters, represented by epilson)
- Pump Efficiency (Percent represented as decimal)

Once this information is input, the model calculates the server temperature, energy usage to run the components of the respective coolying system, the total energy usage of the cooling, and the annual cost. This visualizes some of, if not the most important data for a data center owner to monitor. The model does these calculations by using an equation to relate all the input parameters to calculate the server temperature. The fundamental equation is T_Server (where _ indicates subscript) = T_Initial + deltaT * Factor of Inefficiency. This basic equation applies to both air and liquid-cooled systems, given the difference in calculating those variables for the different methods. T_Server indicates the temperature of the server after the cooling, T_Initial represents the intitial temperature of the medium of cooling (air or liquid), deltaT represents the difference in temperature from before cooling to after cooling, and the factor of inefficiency is a multiplier to represent how the final heat is affected by an inefficiency, whether that be accumulation of dust or degradation of server based on runtime.