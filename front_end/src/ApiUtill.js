export default class ApiUtill{
    static url_root = process.env.NODE_ENV === 'production' 
        ? 'http://api.wuhumodeltest.com/'
        : 'http://127.0.0.1:5000/'
    static url_gpt="ask_gpt"
    static url_ourmodel="ask_ourmodel"
    static url_xxmodel="ask_xxmodel"
    static url_rating="rate"
}
