package edu.harvard.cs50.pokedex;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.media.Image;
import android.os.AsyncTask;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.android.volley.Request;
import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.VolleyError;
import com.android.volley.toolbox.JsonObjectRequest;
import com.android.volley.toolbox.Volley;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;

public class PokemonActivity extends AppCompatActivity {
    private TextView nameTextView;
    private TextView numberTextView;
    private TextView type1TextView;
    private TextView type2TextView;
    private TextView detailTextView;
    private String url;
    private RequestQueue requestQueue;
    boolean pokemon_state;
    ImageView pokeImage;
    Button catch_button;
    String PokeName;


    @SuppressLint("SetTextI18n")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_pokemon);

        requestQueue = Volley.newRequestQueue(getApplicationContext());
        url = getIntent().getStringExtra("url");
        nameTextView = findViewById(R.id.pokemon_name);
        numberTextView = findViewById(R.id.pokemon_number);
        type1TextView = findViewById(R.id.pokemon_type1);
        type2TextView = findViewById(R.id.pokemon_type2);
        pokeImage = findViewById(R.id.pokeImage);
        catch_button = findViewById(R.id.catch_button);
        PokeName = nameTextView.getText().toString();
        detailTextView = findViewById(R.id.description);
        load();
        update();
    }

    @SuppressLint("SetTextI18n")
    public void toggleCatch(View view) {
        if (pokemon_state){
            getPreferences(Context.MODE_PRIVATE).edit().putBoolean(PokeName, false).apply();
        }
        else{
            getPreferences(Context.MODE_PRIVATE).edit().putBoolean(PokeName, true).apply();
        }
        update();
    }


    @SuppressLint("SetTextI18n")
    public void update(){
        pokemon_state = getPreferences(Context.MODE_PRIVATE).getBoolean(PokeName, false);
        if (pokemon_state){
            catch_button.setText("Catch");
        }
        else {
            catch_button.setText("Release");
        }
    }

    public void load() {
        type1TextView.setText("");
        type2TextView.setText("");

        JsonObjectRequest request = new JsonObjectRequest(Request.Method.GET, url, null, new Response.Listener<JSONObject>() {
            @SuppressLint("DefaultLocale")
            @Override
            public void onResponse(JSONObject response) {
                try {
                    nameTextView.setText(response.getString("name"));
                    numberTextView.setText(String.format("#%03d", response.getInt("id")));
                    String url = response.getJSONObject("sprites").getString("front_default");
                    new DownloadSpriteTask(pokeImage).execute(url);
                    loadDetails(response.getJSONObject("species").getString("url"));

                    JSONArray typeEntries = response.getJSONArray("types");
                    for (int i = 0; i < typeEntries.length(); i++) {
                        JSONObject typeEntry = typeEntries.getJSONObject(i);
                        int slot = typeEntry.getInt("slot");
                        String type = typeEntry.getJSONObject("type").getString("name");

                        if (slot == 1) {
                            type1TextView.setText(type);
                        }
                        else if (slot == 2) {
                            type2TextView.setText(type);
                        }
                    }
                } catch (JSONException e) {
                    Log.e("cs50", "Pokemon json error", e);
                }

            }
        }, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                Log.e("cs50", "Pokemon details error", error);
            }
        });


        requestQueue.add(request);

    }

    public void loadDetails(String url){
        detailTextView.setText("");

        JsonObjectRequest request2 = new JsonObjectRequest(Request.Method.GET, url, null, new Response.Listener<JSONObject>() {
            @Override
            public void onResponse(JSONObject response) {
                try {
                    Log.d("try-success", "onResponse: im in ");
                    JSONArray struct = response.getJSONArray("flavor_text_entries");
                    for (int i = 0; i < struct.length(); i++){
                        if (struct.getJSONObject(i).getJSONObject("language").getString("name").equals("en")){
                            detailTextView.setText(struct.getJSONObject(i).getString("flavor_text"));
                            break;
                        }
                    }
                } catch (JSONException e) {
                    Log.d("gand faad", "fuck ho gaya re baba!!");
                    e.printStackTrace();
                }
            }
        }, new Response.ErrorListener() {
            @Override
            public void onErrorResponse(VolleyError error) {
                Log.e("cs50", "Pokemon details error", error);
            }
        });

        requestQueue.add(request2);
    }

    private class DownloadSpriteTask extends AsyncTask<String, Void, Bitmap> {
        ImageView image;
        public DownloadSpriteTask(ImageView image){
            this.image = image;
        }
        @Override
        protected Bitmap doInBackground(String... strings) {
            try {
                URL url = new URL(strings[0]);
                return BitmapFactory.decodeStream(url.openStream());
            }
            catch (IOException e) {
                Log.e("cs50", "Download sprite error", e);
                return null;
            }
        }

        @Override
        protected void onPostExecute(Bitmap bitmap) {
            image.setImageBitmap(bitmap);
        }
    }
}

