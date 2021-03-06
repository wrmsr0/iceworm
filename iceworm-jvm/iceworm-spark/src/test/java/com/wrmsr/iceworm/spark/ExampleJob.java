package com.wrmsr.iceworm.spark;

import org.apache.hadoop.mapred.TextOutputFormat;
import org.apache.spark.SparkConf;
import org.apache.spark.api.java.JavaPairRDD;
import org.apache.spark.api.java.JavaRDD;
import org.apache.spark.api.java.JavaSparkContext;
import org.apache.spark.api.java.Optional;
import org.apache.spark.api.java.function.PairFunction;
import scala.Tuple2;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class ExampleJob
{
    private final JavaSparkContext sc;

    public ExampleJob(JavaSparkContext sc)
    {
        this.sc = sc;
    }

    public static final PairFunction<Tuple2<Integer, Optional<String>>, Integer, String> KEY_VALUE_PAIRER = (a) -> {
        // a._2.isPresent()
        return new Tuple2<>(a._1, a._2.get());
    };

    public static JavaRDD<Tuple2<Integer, Optional<String>>> joinData(JavaPairRDD<Integer, Integer> t, JavaPairRDD<Integer, String> u)
    {
        JavaRDD<Tuple2<Integer, Optional<String>>> leftJoinOutput = t.leftOuterJoin(u).values().distinct();
        return leftJoinOutput;
    }

    public static JavaPairRDD<Integer, String> modifyData(JavaRDD<Tuple2<Integer, Optional<String>>> d)
    {
        return d.mapToPair(KEY_VALUE_PAIRER);
    }

    public static Map<Integer, Long> countData(JavaPairRDD<Integer, String> d)
    {
        Map<Integer, Long> result = d.countByKey();
        return result;
    }

    public JavaPairRDD<String, String> run(String t, String u)
    {
        JavaRDD<String> transactionInputFile = sc.textFile(t);
        JavaPairRDD<Integer, Integer> transactionPairs = transactionInputFile.mapToPair((s) -> {
            String[] transactionSplit = s.split("\t");
            return new Tuple2<>(Integer.valueOf(transactionSplit[2]), Integer.valueOf(transactionSplit[1]));
        });

        JavaRDD<String> customerInputFile = sc.textFile(u);
        JavaPairRDD<Integer, String> customerPairs = customerInputFile.mapToPair((s) -> {
            String[] customerSplit = s.split("\t");
            return new Tuple2<>(Integer.valueOf(customerSplit[0]), customerSplit[3]);
        });

        Map<Integer, Long> result = countData(modifyData(joinData(transactionPairs, customerPairs)));

        List<Tuple2<String, String>> output = new ArrayList<>();
        for (Map.Entry<Integer, Long> entry : result.entrySet()) {
            output.add(new Tuple2<>(entry.getKey().toString(), String.valueOf((long) entry.getValue())));
        }

        JavaPairRDD<String, String> outputRdd = sc.parallelizePairs(output);
        return outputRdd;
    }

    public static void main(String[] args)
            throws Exception
    {
        // UserDefinedFunction mode = udf(
        //         (Seq<String> ss) -> ss.headOption(), DataTypes.StringType
        // );
        //
        // df.select(mode.apply(col("vs"))).show();

        JavaSparkContext sc = new JavaSparkContext(new SparkConf().setAppName("SparkJoins").setMaster("local"));
        ExampleJob job = new ExampleJob(sc);
        JavaPairRDD<String, String> outputRdd = job.run(args[0], args[1]);
        outputRdd.saveAsHadoopFile(args[2], String.class, String.class, TextOutputFormat.class);
        sc.close();
    }
}
