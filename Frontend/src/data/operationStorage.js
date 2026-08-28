// ==========================================
// VayuNetra Operation Storage
// ==========================================
//
// Handles:
// - Active operation
// - Mission history
// - Saving operations
// - Moving operations to history
// - Deleting history
//
// Uses browser localStorage so the demo
// survives page refreshes.
// ==========================================


// ==========================================
// STORAGE KEYS
// ==========================================

const ACTIVE_OPERATION_KEY =
  "vayunetra_active_operation";

const HISTORY_KEY =
  "vayunetra_operation_history";


// ==========================================
// ACTIVE OPERATION
// ==========================================

export function getActiveOperation() {

  try {

    const saved =
      localStorage.getItem(
        ACTIVE_OPERATION_KEY
      );

    if (!saved) {
      return null;
    }

    return JSON.parse(saved);

  } catch (error) {

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

export function saveActiveOperation(operation) {

  try {

    localStorage.setItem(
      ACTIVE_OPERATION_KEY,
      JSON.stringify(operation)
    );

  } catch (error) {

    console.error(
      "Unable to save active operation:",
      error
    );

  }

}


// ==========================================
// CLEAR ACTIVE OPERATION
// ==========================================

export function clearActiveOperation() {

  try {

    localStorage.removeItem(
      ACTIVE_OPERATION_KEY
    );

  } catch (error) {

    console.error(
      "Unable to clear active operation:",
      error
    );

  }

}


// ==========================================
// GET HISTORY
// ==========================================

export function getHistory() {

  try {

    const saved =
      localStorage.getItem(
        HISTORY_KEY
      );

    if (!saved) {
      return [];
    }

    const history =
      JSON.parse(saved);

    return Array.isArray(history)
      ? history
      : [];

  } catch (error) {

    console.error(
      "Unable to read operation history:",
      error
    );

    return [];

  }

}


// ==========================================
// ADD OPERATION TO HISTORY
// ==========================================

export function addToHistory(operation) {

  try {

    const history =
      getHistory();


    /*
      Add newest operation at the top.
    */

    const updatedHistory = [
      operation,
      ...history
    ];


    localStorage.setItem(
      HISTORY_KEY,
      JSON.stringify(
        updatedHistory
      )
    );


  } catch (error) {

    console.error(
      "Unable to add operation to history:",
      error
    );

  }

}


// ==========================================
// DELETE FROM HISTORY
// ==========================================

export function deleteFromHistory(operationId) {

  try {

    const history =
      getHistory();


    const updatedHistory =
      history.filter(
        operation =>
          operation.id !== operationId
      );


    localStorage.setItem(
      HISTORY_KEY,
      JSON.stringify(
        updatedHistory
      )
    );


  } catch (error) {

    console.error(
      "Unable to delete operation:",
      error
    );

  }

}


// ==========================================
// CLEAR ALL HISTORY
// ==========================================
//
// Not currently used by the UI,
// but useful later if needed.
// ==========================================

export function clearHistory() {

  try {

    localStorage.removeItem(
      HISTORY_KEY
    );

  } catch (error) {

    console.error(
      "Unable to clear history:",
      error
    );

  }

}