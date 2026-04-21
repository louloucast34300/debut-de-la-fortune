'use server'

export async function register_action(formData:FormData){
    console.log("ici")
    const url = `${process.env.BACKEND_URL}/api/v1/auth/register`
    try{
        const response = fetch(url, {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(Object.fromEntries(formData))
        })
    }catch(e){
        const errorMessage = e instanceof Error ? e.message : String(e)
        return {"success":false, "message":errorMessage}
    }
}