'use server'

export async function register_action(formData:FormData){
    const url = `${process.env.BACKEND_URL}/api/v1/auth/register`
    try{
        const response = await fetch(url, {
            method : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(Object.fromEntries(formData))
        })
        const data = await response.json()
        if(data.success === true){
            return {"success":true, "message":"utilisateur enregistré"}
        }
    }catch(e){
        const errorMessage = e instanceof Error ? e.message : String(e)
        return {"success":false, "message":errorMessage}
    }
}