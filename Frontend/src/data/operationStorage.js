// ==========================================
// VayuNetra Operation Storage
// ==========================================
//
// Handles:
// - Active operation persistence
// - Mission history
// - Updating missions
// - Moving stopped missions to history
//
// Uses browser localStorage.
//
// Mission remains until:
// 1. Operator stops mission
// 2. 4 hour safety timeout
//
// ==========================================



// ==========================================
// STORAGE KEYS
// ==========================================

const ACTIVE_OPERATION_KEY =
    "vayunetra_active_operation";


const HISTORY_KEY =
    "vayunetra_operation_history";



// ==========================================
// MAX OPERATION TIME
// ==========================================

const MAX_OPERATION_TIME =
    4 * 60 * 60 * 1000;



// ==========================================
// GET ACTIVE OPERATION
// ==========================================

export function getActiveOperation(){

    try {


        const saved =
            localStorage.getItem(
                ACTIVE_OPERATION_KEY
            );


        if(!saved){
            return null;
        }


        const operation =
            JSON.parse(saved);



        // Safety timeout
        if(operation.startedAt){

            const age =
                Date.now()
                -
                new Date(
                    operation.startedAt
                ).getTime();



            if(age > MAX_OPERATION_TIME){

                addToHistory({

                    ...operation,

                    status:
                        "COMPLETED",

                    completedAt:
                        new Date().toISOString()

                });


                clearActiveOperation();


                return null;

            }

        }



        return operation;



    }
    catch(error){


        console.error(
            "Unable to read active operation:",
            error
        );


        return null;

    }

}




// ==========================================
// SAVE ACTIVE OPERATION
// ==========================================

export function saveActiveOperation(operation){

    try{


        localStorage.setItem(

            ACTIVE_OPERATION_KEY,

            JSON.stringify(
                operation
            )

        );


    }
    catch(error){


        console.error(
            "Unable to save active operation:",
            error
        );


    }

}





// ==========================================
// UPDATE ACTIVE OPERATION
// ==========================================

export function updateActiveOperation(updates){

    try{


        const current =
            getActiveOperation();



        if(!current){

            return null;

        }



        const updated = {


            ...current,


            ...updates,


            updatedAt:
                new Date().toISOString()


        };



        saveActiveOperation(
            updated
        );



        return updated;



    }
    catch(error){


        console.error(
            "Unable to update operation:",
            error
        );


        return null;

    }

}





// ==========================================
// CLEAR ACTIVE OPERATION
// ==========================================

export function clearActiveOperation(){

    try{


        localStorage.removeItem(
            ACTIVE_OPERATION_KEY
        );


    }
    catch(error){


        console.error(
            "Unable to clear active operation:",
            error
        );


    }

}





// ==========================================
// GET HISTORY
// ==========================================

export function getHistory(){

    try{


        const saved =
            localStorage.getItem(
                HISTORY_KEY
            );


        if(!saved){

            return [];

        }



        const history =
            JSON.parse(saved);



        return Array.isArray(history)
            ? history
            : [];



    }
    catch(error){


        console.error(
            "Unable to read history:",
            error
        );


        return [];

    }

}





// ==========================================
// ADD TO HISTORY
// ==========================================

export function addToHistory(operation){

    try{


        const history =
            getHistory();



        const updated = [

            operation,

            ...history

        ];



        localStorage.setItem(

            HISTORY_KEY,

            JSON.stringify(
                updated
            )

        );


    }
    catch(error){


        console.error(
            "Unable to add history:",
            error
        );


    }

}





// ==========================================
// DELETE FROM HISTORY
// ==========================================

export function deleteFromHistory(operationId){

    try{


        const history =
            getHistory();



        const updated =

            history.filter(

                operation =>

                    operation.id !== operationId

            );



        localStorage.setItem(

            HISTORY_KEY,

            JSON.stringify(
                updated
            )

        );



    }
    catch(error){


        console.error(
            "Unable to delete history:",
            error
        );


    }

}





// ==========================================
// CLEAR HISTORY
// ==========================================

export function clearHistory(){

    try{


        localStorage.removeItem(
            HISTORY_KEY
        );


    }
    catch(error){


        console.error(
            "Unable to clear history:",
            error
        );


    }

}