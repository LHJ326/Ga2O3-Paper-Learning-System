# P001 Knowledge Summary

## Research Objective

- There is a need to develop novel energy-efficient 2D floating-gate memory with high performance [E00026].
- The work targets an energy-efficient DUV light programming FG memory based on ultrathin MoS2/β-Ga2O3/multilayer graphene (MLG) for artificial visual neuromorphic systems [E00076].
- Optical-stimulated artificial synapses based on FG transistors are urgently needed [E00021].
- It aims to achieve multilevel storage under DUV light with low power and low photon number while maintaining robust anti-interference and storage performance [E00076].
- Optoelectrical synapses based on memory devices for brain-inspired computing face high power consumption (large programming voltage, high optical power density) and difficulty avoiding interference from solar radiation, potentially limiting their applications in artificial neural systems (E00013). [E00013]

## Core Innovations

- It utilizes the unique photosensitive dielectric properties of beta-Ga2O3 to achieve low-voltage and solar-blind operation (E00013). [E00013]
- The work offers a new scheme for constructing an ultrathin neuromorphic storage and computing integrated system using a DUV photosensitive dielectric [E00027].
- The unique photosensitive characteristics of the high-κ dielectric β-Ga2O3 introduce a novel optoelectronic mechanism within FG memory devices [E00049].
- The innovative design provides new insights for van der Waals heterostructure optical memory devices based on Ga2O3 photosensitive dielectric and a new building block for constructing energy-efficient artificial visual neuromorphic systems with high performance [E00076].
- The work proposes a novel optoelectrical floating gate memory based on MoS2/beta-Ga2O3/multilayer graphene (E00013). [E00013]
- The proposed device uses an ultrathin MoS2/β-Ga2O3/MLG van der Waals heterojunction and β-Ga2O3 as a photosensitive dielectric, unlike present floating-gate memories used in neuromorphic systems [E00024][E00026].
- Operation in the DUV solar-blind region (220–280 nm) is proposed to avoid interference from solar radiation [E00026].
- The architecture uses MLG as the floating gate, β-Ga2O3 as the photosensitive dielectric layer, and MoS2 as the channel. [E00028][E00030]

## Experimental Results

- Under electrical pulse, the device exhibits a current switching ratio >10^6, storage window ratio of 78.44%, retention >10^3 s, and endurance >1000 programming/erasing cycles at a P/E voltage of ±40 V and an equivalent electric field intensity of 7.94 MV cm−1 [E00027].
- Storage performance included a current switching ratio exceeding 10^6, a storage window ratio of 78.44%, retention surpassing 10^3 s, and endurance exceeding 1000 programming/erasing cycles under a low programming/erasing voltage of ±40 V [E00076].
- Multilevel storage is achieved by controlling 254 nm DUV light with a low power of 254.4 pJ at 0 V, requiring 3.25×10^8 photons per programming operation, which is much smaller than most present works [E00027].
- The device exhibits a current switching ratio of 10^6 at a low programming/erasing voltage of ±40 V in a small equivalent electric field intensity of 7.94 MV cm−1, and a tiny photon number of 3.25 × 10^8, which is much smaller than that of most present works. [E00055]
- Retention stability, endurance performance, storage charge density versus Vbg scanning range, and switching ratios under specified pulse/voltage conditions were reported [E00169].
- The device exhibits an excellent current switching ratio of 10^6 only at a low programming/erasing voltage of ±40 V (E00013). [E00013]
- The device possesses a strong anti-interference ability and can operate in the solar-blind region (254 nm) only with a low power of 254.4 pJ (0 V) (E00013). [E00013]
- Due to the large single photon energy at the short wavelength, the photon number used per programming operation is 3.25 × 10^8, much smaller than that of most present works (E00013). [E00013]
- The neural network model constructed with the memory device achieves an accuracy of 91.07% for image recognition (E00013). [E00013]
- The VGG-8 model based on the MoS2/β-Ga2O3/MLG floating-gate memory achieves 91.07% recognition accuracy on CIFAR-10 dataset images [E00027].
- The ratio of the memory window range and the sweeping voltage range (W.R./S.R.) positively correlated with Vbg,max, reaching 78.44% when Vbg,max = 60 V was applied. [E00042]
- An ideal P/E operating pulse width of 0.1 s for the device was suggested as optimal, allowing a high on/off ratio of 5 × 10^6 to be tightly controlled [E00046].

## Methodology

- The device uses electrical pulses and 254 nm pulse DUV light, with photoelectric hybrid modulation for synaptic properties, and a VGG-8 model based on the device is evaluated on CIFAR-10 dataset images [E00027].
- Characterization included Raman spectra measured in MoS2/β-Ga2O3/MLG, MoS2, and MLG regions; optical microscopy; SEM EDS elemental mapping of Ga and O; EDS spectrum; and AFM imaging/height profiling. [E00030][E00031]
- A VGG-8 network was used for object recognition and classification on image data derived from CIFAR-10. [E00069]
- Characterization used Raman spectroscopy (invia) with 532 nm laser to confirm materials; optical microscopy (BA3 10MET-T, Motic) and AFM (Dimension FastScan from Bruker); electrical and optoelectronic measurements at room temperature via a four-probe station with two source meters (Keithley 2636B and Keithley 2611B); optoelectronic measurements used 405, 520, and 635 nm lasers and 254 nm light from an LED lamp [E00079].
- The designed optoelectronic memory was fabricated by a MoS2/β-Ga2O3/MLG heterostructure. [E00028]
- The schematic fabrication process of the MoS2/β-Ga2O3/MLG floating-gate memory is displayed in Figure S1 (Supporting Information). [E00028][E00031]
- To investigate the performance of the 2D β-Ga2O3 dielectric layer, a single MoS2 field-effect transistor (FET) was realized by connecting MLG as a gate electrode, and its transfer characteristics (Ids–Vcg) were measured. [E00032]
- Measured Igs across the dielectric layer to analyze the transport mechanism of the MoS2/β-Ga2O3/MLG device. [E00038]

## Reported Limitations

- P/E operations become increasingly difficult with decreasing pulse widths [E00046].
- Tunneling-based non-volatile memory devices often have compromised endurance following repeated cycles of erasure and programming [E00050].
- Programming cannot be realized solely by applying 254 nm light pulses without an internal electric field [E00053].
- Under visible light, photogenerated electrons from MoS2 cannot tunnel through β-Ga2O3, leading to an increase in output current instead of a decrease during programming [E00053].
- Carriers originating from MoS2 encounter significant challenges in penetrating the dielectric layer [E00054].
