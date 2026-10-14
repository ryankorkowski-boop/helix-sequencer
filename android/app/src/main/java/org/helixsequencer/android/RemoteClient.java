package org.helixsequencer.android;

import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;

/** Paired HTTP transport. Cleartext is restricted to literal private addresses. */
public final class RemoteClient {
    private final String base,key;
    public RemoteClient(String endpoint,String key)throws Exception{
        URL url=new URL(endpoint.trim());String protocol=url.getProtocol(),host=url.getHost();
        if(!protocol.equals("https")&&!protocol.equals("http"))throw new IOException("Use an http:// or https:// desktop address");
        if(url.getUserInfo()!=null||url.getQuery()!=null||url.getRef()!=null||!url.getPath().isEmpty()&&!url.getPath().equals("/"))throw new IOException("Enter the desktop address and port without a path or password");
        if(protocol.equals("http")){
            String literal=host.replace("[","").replace("]","");
            if(!literal.matches("[0-9.]+")&&!literal.matches("[0-9a-fA-F:]+"))throw new IOException("For HTTP, enter the desktop's local IP address; use HTTPS for a hostname");
            InetAddress address=InetAddress.getByName(literal);byte[] bytes=address.getAddress();boolean ula=bytes.length==16&&(bytes[0]&0xfe)==0xfc;
            if(!address.isLoopbackAddress()&&!address.isSiteLocalAddress()&&!address.isLinkLocalAddress()&&!ula)throw new IOException("Public desktop addresses require HTTPS");
        }
        if(key.trim().length()<32)throw new IOException("Paste the complete pairing key from desktop Helix");
        this.base=endpoint.trim().replaceAll("/+$","");this.key=key.trim();
    }
    private HttpURLConnection open(String method,String path)throws Exception{
        HttpURLConnection connection=(HttpURLConnection)new URL(base+path).openConnection();connection.setRequestMethod(method);connection.setConnectTimeout(8000);connection.setReadTimeout(120000);
        connection.setInstanceFollowRedirects(false);connection.setRequestProperty("Authorization","Bearer "+key);return connection;
    }
    private JSONObject response(HttpURLConnection connection)throws Exception{
        int code=connection.getResponseCode();InputStream stream=code>=400?connection.getErrorStream():connection.getInputStream();ByteArrayOutputStream buffer=new ByteArrayOutputStream();
        if(stream!=null)try(InputStream in=stream){byte[] bytes=new byte[8192];int n;while((n=in.read(bytes))!=-1){buffer.write(bytes,0,n);if(buffer.size()>2*1024*1024)throw new IOException("Desktop response too large");}}
        JSONObject result;try{result=new JSONObject(buffer.toString("UTF-8"));}catch(JSONException e){throw new IOException("Unexpected desktop response (HTTP "+code+")");}
        if(code<200||code>=300)throw new IOException(result.optString("error","Desktop HTTP "+code));return result;
    }
    public JSONObject json(String method,String path,JSONObject data)throws Exception{
        HttpURLConnection connection=open(method,path);try{
            if(data!=null){byte[] bytes=data.toString().getBytes(StandardCharsets.UTF_8);connection.setDoOutput(true);connection.setFixedLengthStreamingMode(bytes.length);connection.setRequestProperty("Content-Type","application/json");try(OutputStream out=connection.getOutputStream()){out.write(bytes);}}
            return response(connection);
        }finally{connection.disconnect();}
    }
    public void upload(String identity,String role,File file)throws Exception{
        if(!identity.matches("[0-9a-f-]{36}")||!role.matches("audio|layout|template|lor|networks|routing"))throw new IOException("Invalid upload");
        HttpURLConnection connection=open("PUT","/v1/jobs/"+identity+"/files/"+role);try{
            connection.setDoOutput(true);connection.setFixedLengthStreamingMode(file.length());connection.setRequestProperty("Content-Type","application/octet-stream");
            try(InputStream in=new FileInputStream(file);OutputStream out=connection.getOutputStream()){EngineService.copy(in,out);}response(connection);
        }finally{connection.disconnect();}
    }
    public void download(String identity,String type,File target)throws Exception{
        if(!identity.matches("[0-9a-f-]{36}")||!type.matches("bundle|preview"))throw new IOException("Invalid download");
        HttpURLConnection connection=open("GET","/v1/jobs/"+identity+"/"+type);File part=new File(target+".part");try{
            int code=connection.getResponseCode();if(code!=200){response(connection);throw new IOException("Download HTTP "+code);}
            if(connection.getContentLengthLong()>1024L*1024*1024)throw new IOException("Desktop download exceeds1GB");
            try(InputStream in=connection.getInputStream();OutputStream out=new FileOutputStream(part)){byte[] buffer=new byte[65536];long count=0;int n;while((n=in.read(buffer))!=-1){count+=n;if(count>1024L*1024*1024)throw new IOException("Desktop download exceeds1GB");out.write(buffer,0,n);}}
            java.nio.file.Files.move(part.toPath(),target.toPath(),java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }finally{part.delete();connection.disconnect();}
    }
}
