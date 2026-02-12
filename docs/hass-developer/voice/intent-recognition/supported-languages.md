import languages from '!!yaml-loader!../../../intents/languages.yaml';
import intents from '!!yaml-loader!../../../intents/intents.yaml';

If you don't see your language below, [help us translate!](/docs/voice/intent-recognition/contributing)

For a full progress report per language, [click here.](https://ohf-voice.github.io/intents/)

<>
  
    
      
        Code
        Language
        Leader
        Links
      
    
    
      {
        Object.entries(languages).map(
          ([language, info]) =>
            
              
                <code>{language}</code>
              
              
                {info.nativeName}
              
              
                {info.leaders?.length &&
                    info.leaders.map((leader, idx) =>
                      <>
                        {!!idx && ', '}
                        {leader}
                      </>
                    )}
              
              
                Sentences
              
            
        )
      }
    
  
</>

[This page is automatically generated based on the Intents repository.](https://github.com/home-assistant/intents/blob/main/languages.yaml)
