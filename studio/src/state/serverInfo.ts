export type t = {
  studioProjectsPath: string;
};

export async function get(backendURL: string): Promise<t> {
  try {
    const response = await fetch(backendURL + '/server_info');
    const result: t = await response.json();
    console.log('Got server info!', result);
    return result;
  } catch (e) {
    console.error(e);
    throw e;
  }
}
