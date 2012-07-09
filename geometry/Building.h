/*
 * File:   Building.h
 * Author: andrea
 *
 * Created on 1. October 2010, 09:25
 */

#ifndef _BUILDING_H
#define	_BUILDING_H

#include <string>
#include <vector>
#include <fstream>
#include <cfloat>
#include <omp.h>

#include "Room.h"
#include "../general/Macros.h"
#include "../routing/Routing.h"
#include "../pedestrian/Pedestrian.h"
#include "../geometry/Transition.h"
#include "../mpi/LCGrid.h"
#include "../mpi/MPIDispatcher.h"

using namespace std;

class MPIDispatcher;

class Building {
private:
    string pCaption; // Name des Projekts
    Routing* pRouting;
    vector<Room*> pRooms; // Liste der Räume
    vector<Pedestrian*> pAllPedestians;
    LCGrid* pLinkedCellGrid;
    // this is only for the Hermes Project
    bool pSubroomConnectionMap[16][130][16][130];

    // pedestrians pathway
    bool pSavePathway;
    ofstream PpathWayStream;

    //MPI
	MPIDispatcher* pMPIDispatcher;
	vector<Pedestrian*> pPedtransfering;

    // wird nur innerhalb von Building benötigt
    void LoadHeader(ifstream* buildingfile, int* i);
    void LoadRooms(ifstream* buildingfile, int* i);
    void LoadRoom(ifstream* buildingfile, int* i);
    void StringExplode(string str, string separator, vector<string>* results);

public:
    // Konstruktor
    Building();
    Building(const Building& orig);
    virtual ~Building();

    // Setter -Funktionen
    void SetCaption(string s);
    void SetRouting(Routing* r);
    void SetAllRooms(const vector<Room*>& rooms);
    void SetRoom(Room* room, int index);
    /// delete the ped from the ped vector
    void DeletePedestrian(Pedestrian* ped);
    /// delete the ped from the simulation
    void DeletePedFromSim(Pedestrian* ped);
    void AddPedestrian(Pedestrian* ped);

    // Getter - Funktionen
    string GetCaption() const;
    Routing* GetRouting() const;
    const vector<Room*>& GetAllRooms() const;
    const vector<Pedestrian*>& GetAllPedestrians() const;
    int GetAnzRooms() const;
    Room* GetRoom(int index) const; // Gibt Raum der Nummer "index" zurueck
    Room* GetRoom(string caption)const;
    Transition* GetTransition(string caption) const;
    Crossing* GetGoal(string caption) const;
    int GetAnzPedestrians() const;
    LCGrid* GetGrid() const;

    // Sonstiges
    void InitGeometry();
    void InitGrid(double cellSize);
    void InitRoomsAndSubroomsMap();
    void InitPhiAllPeds(); // Initialisiert die Ausrichtung der Ellipse
    void InitSavePedPathway(string filename);
    void AddRoom(Room* room);
    void Update();
    void UpdateGrid();
    void AddSurroundingRoom(); // add a final room (outside or world), that encompasses the complete geometry


    // Ein-Ausgabe
    void LoadBuilding(string filename); // Laedt Geometrie-Datei
    void LoadStatesOfRooms(string filename);
    void LoadStatesOfDoors(string filename);
    void WriteToErrorLog() const;

	// MPI:
	void SetMPIDispatcher(MPIDispatcher *mpi);
	MPIDispatcher* GetMPIDispatcher() const;
	void AddPedestrianWaitingForTransfer(Pedestrian* ped);
	void GetPedestriansTransferringToRoom(int roomID,vector<Pedestrian*>& transfer);
	void ClearTranfer();// just for control should always be empty
	void DumpSubRoomInRoom(int room, int sub);
	//remove all pedestrians which has more less than 10 cm for the last 20 seconds
	void CleanUpTheScene();


	// saving computation
	bool IsDirectlyConnected(int room1, int subroom1,int room2, int subroom2);

};

#endif	/* _BUILDING_H */

